def get_file_type(ext: str) -> str:
    extension_mapping = {
        'image': ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff', 'svg', 'webp', 'jfif'],
        'video': ['mp4', 'avi', 'mov', 'mkv', 'flv', 'wmv', 'webm'],
        'document': ['pdf', 'doc', 'docx', 'txt', 'xls', 'xlsx', 'ppt', 'pptx', 'csv'],
        'audio': ['mp3', 'wav', 'aac', 'flac', 'ogg', 'm4a'],
    }

    for file_type, extensions in extension_mapping.items():
        if ext in extensions:
            return file_type

    return 'other'


def content_file_name(instance, filename: str) -> str:
    return '/'.join(['uploads', instance.group.name, filename])


def generate_filename(file, target_format: str) -> str:
    prompt = f"""
    Based on the content of the file below, generate a filename that matches the target format: {target_format}.
    Return only the filename. If no date is provided in the content or in metadata, do not include a date in the filename.
    You can use the following file metadata for context:
    {file.get_meta_data()}
    """

    filename = file.data_extraction(prompt)

    return filename
