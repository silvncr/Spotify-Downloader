from base64 import b64encode
from getpass import getuser
from json import dump, load
from os import makedirs
from pytube import YouTube
from re import findall
from requests import get, post
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import urlopen
default_location = r'C:\Users\{}\Music'.format(getuser())
def get_playlists(spotify_url):
	with open('SECRETS.json', 'r') as f:
		spotify_key = load(f)['SPOTIFY_KEY']
	playlist_id = spotify_url.split('/')[-1].split('?')[0]
	r = get(f"https://api.spotify.com/v1/playlists/{playlist_id}", headers={'Authorization': f'Bearer {spotify_key}'})
	if r.status_code in [400, 401]:
		raise TypeError('Invalid Spotify Token')
	returned_tracks = {}
	playlist_name = r.json()['name']
	r = get(f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks", headers={'Authorization': f'Bearer {spotify_key}'})
	data = r.json()
	tracks = data['items']
	while data['next']:
		r = get(data['next'], headers={'Authorization': f'Bearer {spotify_key}'})
		data = r.json()
		tracks = tracks + data['items']
	for track in tracks:
		song_name = track['track']['name']
		artists = [artist['name'] for artist in track['track']['artists']]
		artist_name = ' '.join(artists)
		try:
			query_string = urlencode({'search_query': f'{artist_name} {song_name}'})
			htm_content = urlopen(f'http://www.youtube.com/results?{query_string}')
			search_results = findall(r'/watch\?v=(.{11})', htm_content.read().decode())
			returned_tracks[f'{song_name}'] = f'http://www.youtube.com/watch?v={search_results[0]}'
		except HTTPError:
			print(f'Couldn\'t download "{song_name}", continuing...')
			continue
	return playlist_name, returned_tracks
def get_access_token():
	with open('SECRETS.json', 'r') as f:
		load_file = load(f)
		spotify_client_id = load_file['spotify_client_id']
		spotify_client_secret = load_file['spotify_client_secret']
	headers = {
		'Authorization': f'Basic {b64encode(f"{spotify_client_id}:{spotify_client_secret}".encode()).decode()}',
	}
	data = {
		'grant_type': 'client_credentials'
	}
	r = post('https://accounts.spotify.com/api/token', headers=headers, data=data)
	token = r.json()['access_token']
	updated_dict = {
		'spotify_client_id': spotify_client_id,
		'spotify_client_secret': spotify_client_secret,
		'SPOTIFY_KEY': token
	}
	with open('SECRETS.json', 'w') as f:
		dump(updated_dict, f, indent=4)
def downloader(spotify_url, location):
	print('\nAttempting to find song links...')
	try:
		track = get_playlists(spotify_url)
	except TypeError:
		get_access_token()
		track = get_playlists(spotify_url)
	path = f'{location}\\{track[0].replace(" ", "-")}'
	try:
		makedirs(path)
	except FileExistsError:
		print(f'\nFolder already exists; located at: "{path}". Continuing...')
	else:
		print(f'\nFolder created successfully! Located at: "{path}".')
	dict_of_playlist = track[1]
	print('\nDownloading songs from playlist...\n')
	for url_name in dict_of_playlist:
		try:
			yt = YouTube(dict_of_playlist[url_name])
			video = yt.streams.filter(only_audio=True).first()
			video.download(path)
			print(f'Downloaded "{url_name}".')
		except HTTPError:
			print(f'Couldn\'t download "{url_name}", continuing...')
			continue
		except FileExistsError:
			print(f'Song "{url_name}" already exists in this folder, continuing...')
if __name__ == '__main__':
	downloader(input('\nPlease enter the Spotify playlist link.\n\n>'), input(f'\nPlease enter the location to download the songs to.\nLeave text empty for default location: "{default_location}"\n\n>'))
	print('\nDone!')
