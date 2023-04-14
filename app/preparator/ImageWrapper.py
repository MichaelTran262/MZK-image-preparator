from .. import models

class ImageWrapper():

    @classmethod
    def get_images_by_page(self, page = 1):
        images = models.Image.query.paginate(page=page, per_page=10)
        return images