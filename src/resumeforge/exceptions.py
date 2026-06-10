class ResumeForgeError(Exception):
    pass


class DataLoadError(ResumeForgeError):
    pass


class ResumeGenerationError(ResumeForgeError):
    pass
