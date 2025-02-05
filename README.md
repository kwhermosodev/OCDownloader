# OCDownloader

A YouTube downloader focused on downloading and pre-organizing your music collection. Simply create a CSV file detailing your desired subfolders, the correct file naming via the artist-title standard, and the max video width for uniformity.

## Features
- Simple UI
- CSV Template
- Single executable
- Save your CSV and redownload your collection anytime without having to manually reorganize your files.
- Auto convert to MP3 and MP4

## Usage/Examples

1. **Click "Create CSV"**
   - This will create a CSV in the same location as your `.exe` file.

2. **Edit the CSV** using MS Excel or any software available to you. All fields are required unless specified otherwise:
   - Put your custom subfolder(s) (e.g., `MP4` or `MP4\Synthwave Videos`) in the `sub_folder` field.
   - Put the song artist in the `artist` field (optional).
   - Put the song title in the `title` field.
   - Put `audio` for audio files or `video` for video files in the `media_type_audio_or_video` field.
   - Put the max width in pixels in the `max_width_in_pixels` field.
   - For audio media types, the video width can be left blank.
   - Add multiple rows as needed.

3. **Click "Upload CSV"** and choose your edited CSV.

4. **Click "Download from CSV"** to begin downloading.

## Installation

Download the `OCDownloader.zip` from the `bundle/dist` folder.
==[IMPORTANT]== Since my software isn't digitally signed, you will need to excempt it 