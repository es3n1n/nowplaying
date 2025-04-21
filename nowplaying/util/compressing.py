import io

from PIL import Image


TGT_FORMAT = 'JPEG'
TGT_MODE = 'RGB'


# Telegram has a file size limit for song covers.
def compress_to_jpeg(img_data: io.BytesIO, target_size_kb: int, quality_step: int = 5) -> io.BytesIO:
    img: Image.ImageFile.ImageFile | Image.Image = Image.open(img_data)

    valid_format = img.format == TGT_FORMAT
    valid_mode = img.mode == TGT_MODE
    valid_options = valid_format and valid_mode

    if valid_options and img_data.getbuffer().nbytes / 1024 <= target_size_kb:
        return img_data

    quality = 100
    if valid_options:
        quality -= quality_step

    if not valid_mode:
        img = img.convert(TGT_MODE)

    while quality > 0:
        output_buffer = io.BytesIO()
        img.save(output_buffer, format=TGT_FORMAT, quality=quality)

        size_kb = output_buffer.getbuffer().nbytes / 1024
        if size_kb <= target_size_kb:
            return output_buffer

        quality -= quality_step

    return img_data
