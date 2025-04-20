import io

from PIL import Image


# Telegram has a file size limit for song covers.
def compress_jpeg(img_data: io.BytesIO, target_size_kb: int, quality_step: int = 5) -> io.BytesIO:
    if img_data.getbuffer().nbytes / 1024 <= target_size_kb:
        return img_data

    img = Image.open(img_data)
    quality = 100 - quality_step

    while quality > 0:
        output_buffer = io.BytesIO()
        img.save(output_buffer, format='JPEG', quality=quality)

        size_kb = len(output_buffer.getvalue()) / 1024
        if size_kb <= target_size_kb:
            return output_buffer

        quality -= quality_step

    return img_data
