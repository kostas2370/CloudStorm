import logging

logger = logging.getLogger(__name__)

EXTENSION_MAPPING = {
    "image": ["jpg", "jpeg", "png", "gif", "bmp", "tiff", "svg", "webp", "jfif"],
    "video": ["mp4", "avi", "mov", "mkv", "flv", "wmv", "webm"],
    "document": ["pdf", "doc", "docx", "txt", "xls", "xlsx", "ppt", "pptx", "csv"],
    "audio": ["mp3", "wav", "aac", "flac", "ogg", "m4a"],
}

# Archives are uploadable but are unpacked instead of stored, so they stay out of
# EXTENSION_MAPPING and never become a File.file_type of their own.
ARCHIVE_EXTENSIONS = frozenset({".zip"})

ALLOWED_EXTENSIONS = (
    frozenset(
        f".{extension}"
        for extensions in EXTENSION_MAPPING.values()
        for extension in extensions
    )
    | ARCHIVE_EXTENSIONS
)


def get_file_type(ext: str) -> str:
    for file_type, extensions in EXTENSION_MAPPING.items():
        if ext in extensions:
            return file_type

    return "other"


def content_file_name(instance, filename: str) -> str:
    return "/".join(["uploads", instance.group.name, filename])


def generate_filename(file, target_format: str = "") -> str:
    if not target_format:
        target_format = "{random_number}_{title}"

    prompt = f"""
    Based on the content of the file below, generate a filename that matches the target format: {target_format}.
    Return only the filename. If no date is provided in the content or in metadata, do not include a date in the filename.
    You can use the following file metadata for context:
    {file.get_meta_data()} if you can not generate a name just return the name from metadata.
    """
    try:
        filename = file.data_extraction(prompt)
        if not filename:
            return file.name

        file.create_extracted_data(name="filename_generation", data=filename)
    except Exception:
        logger.exception("Filename generation failed for file %s", file.pk)
        filename = file.name

    return filename


def generate_short_description(file):
    prompt = """
     Based on the content of the file below, generate a short description, Maximum 1000 characters.
    """
    short_description = file.data_extraction(prompt)
    if not short_description:
        return None

    file.create_extracted_data(
        name="short_description_generation", data=short_description
    )
    return short_description


def generate_tags(file):
    prompt = """
    Based on the content of the file below, generate tags in the format: x1,x2,x3, etc.
    Return only the tags, nothing else. Be as generic as possible. If you can not generate tags return tag other
    """
    tags = file.data_extraction(prompt)
    if not tags:
        return []

    file.create_extracted_data(name="tags_generation", data=tags)
    return [tag.strip() for tag in tags.split(",") if tag.strip()]


def extract_data(file, user_prompt):
    prompt = f"Extract {user_prompt} from the file content. Return only the data."
    data = file.data_extraction(prompt)
    file.create_extracted_data(name="extracted_data", data=data)
    return data
