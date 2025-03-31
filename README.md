# Spotify-To-YouTube Playlist Converter

My first ever proper project in programming (that wasnt game dev) created during autum 2024
Can convert Spotify Playlists to Youtube playlists and more

## Features
- Convert any public Spotify playlist to a YouTube playlist
- Automatically fetches track details and matches them on YouTube
- Can also display and delete playlists

## Prerequisites
Before you begin, ensure you have the following installed:
- Python 3.x
- [Spotify API credentials](https://developer.spotify.com/dashboard/)
- [YouTube Data API credentials](https://console.cloud.google.com/apis/)

## Installation
Clone the repository and install the required dependencies:
```sh
git clone https://github.com/Lazypupz/Spotify-To-Youtube.git
cd Spotify-To-Youtube
pip install -r requirements.txt
```

## Setup
1. Obtain your Spotify and YouTube API credentials.
2. Place your `credentials.json` file in the root directory.
3. Place your Spotify keys into a `.env` file in the root dir
```sh
SPOTIFYCLIENT_ID=your_spotify_client_key
SPOTIFYCLIENT_SECRET=your_spotify_secret_key
```

## Usage
Run the script with:
```sh
python main.py
```

## Notes
- It takes the same amount of effor for private and public playlists
- The youtube api quota is limited so I tried to optimise it the best i could as a new programmer 

## Contributing
Pull requests and contributions are welcome! Feel free to submit issues or feature requests.

## License
This project is licensed under the MIT License.

## Author
[Lazypupz](https://github.com/Lazypupz)

