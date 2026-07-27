from fastapi import HTTPException, status


class OCRProcessingError(Exception):
    """Raised when the OCR pipeline fails to process an image."""
    pass


class CrawlerError(Exception):
    """Raised when the EPREL crawler encounters an error."""
    pass


class ProductNotFoundError(HTTPException):
    """Raised when a product is not found."""
    def __init__(self, product_id: str) -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product {product_id} not found",
        )


class InvalidFileError(HTTPException):
    """Raised when an uploaded file is invalid."""
    def __init__(self, detail: str = "Invalid file format") -> None:
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
        )
