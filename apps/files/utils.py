import os


def get_file_type(filename):
    extension_mapping = {
        'image': ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff', 'svg', 'webp'],
        'video': ['mp4', 'avi', 'mov', 'mkv', 'flv', 'wmv', 'webm'],
        'document': ['pdf', 'doc', 'docx', 'txt', 'xls', 'xlsx', 'ppt', 'pptx', 'csv'],
        'audio': ['mp3', 'wav', 'aac', 'flac', 'ogg', 'm4a'],
    }

    ext = os.path.splitext(filename)[1][1:].lower()

    for file_type, extensions in extension_mapping.items():
        if ext in extensions:
            return file_type

    return 'other'


def content_file_name(instance, filename):
    return '/'.join(['uploads', instance.group.name, filename])
