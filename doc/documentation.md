# API




# Celery Tasks
## convert_image()

Converts an image from tiff to jpeg. This task is evoked on every tiff file in folder 2 for maximum efficiency because each conversion runs as separate process.

### Parameters

- `rel_file` (path): Path of image relative from folder 2 
    <br>examples:
    ```python
    0001.tiff, konvolut01/0001.tiff
    ```
- `src_file` (path): Absolute path of source TIFF image. (What is rel_file for then?)
- `dst_dir3` (path): Absolute path of folder 3, where new jpeg image will be saved.
- `dst_dir4` (path): Same as dir3, but for folder 4.
- `folder_id` (int): Foreign key of folder where the Image object exists. 
- `uid` (int): Owner of source image.
- `gid` (int): Group ownership of source image.

### Returns

- nothing

### Examples

Let's say we want to prepare images on folder with absolute path `/mnt/book/hamlet`

```python
# converts first page to folder 3 and 4
>>> convert_image(0001.tiff, /mnt/book/hamlet/0001.tiff, /mnt/book/hamlet/3, /mnt/book/hamlet/4)
```
send_to_mzk