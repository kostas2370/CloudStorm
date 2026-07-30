class AIGenerationError(Exception):
    """An AI generation request that cannot be served, safe to report to the client."""


class UnsupportedFileType(AIGenerationError):
    pass


class FileAlreadyGenerating(AIGenerationError):
    pass


class GenerationFailed(AIGenerationError):
    pass
