from flask import Flask, jsonify, redirect, render_template, Response, request
import requests
import base64
import uuid

app = Flask(__name__)

# Dictionary to store audio stream URLs with unique UUID hex codes
audio_streams_dict = {}

all_domains = [
    "vid.puffyan.us", "yt.artemislena.eu", "invidious.projectsegfau.lt",
    "invidious.slipfox.xyz", "invidious.privacydev.net", "vid.priv.au",
    "iv.melmac.space", "iv.ggtyler.dev", "invidious.lunar.icu", "inv.zzls.xyz",
    "inv.tux.pizza", "invidious.protokolla.fi", "onion.tube",
    "inv.in.projectsegfau.lt", "inv.citw.lgbt", "yt.oelrichsgarcia.de",
    "invidious.no-logs.com", "invidious.io.lol", "iv.nboeck.de",
    "invidious.private.coffee", "yt.drgnz.club", "invidious.asir.dev",
    "iv.datura.network", "invidious.fdn.fr", "anontube.lvkaszus.pl",
    "invidious.perennialte.ch", "yt.cdaut.de", "invidious.drgns.space",
    "inv.us.projectsegfau.lt", "invidious.einfachzocken.eu",
    "invidious.nerdvpn.de", "yewtu.be"
]

def xor_encrypt_decrypt(data, key):
  key = key.encode()
  result = bytearray()

  for i, char in enumerate(data):
      result.append(char ^ key[i % len(key)])

  return bytes(result)

def encrypt(youtube_id, key):
  encrypted_data = xor_encrypt_decrypt(youtube_id.encode(), key)
  return encrypted_data.hex()

def decrypt(encrypted_data, key):
  encrypted_data_bytes = bytes.fromhex(encrypted_data)
  decrypted_data = xor_encrypt_decrypt(encrypted_data_bytes, key)
  return decrypted_data.decode()

key = "ergthyjtukytrhewefcdvfgthyjtukytjythrgefawdfevweteryrntsbyrhthhtyiipiolfew"


def get_video_info(video_id):

  for domain in all_domains:
    url = f'https://{domain}/api/v1/videos/{video_id}'
    response = requests.get(url)

    if response.status_code == 200:
      video_info = response.json()

      # Filter and include only the highest quality audio streams
      highest_quality_audio = get_highest_quality_audio(
          video_info.get("adaptiveFormats", []))

      return highest_quality_audio
    else:
      print(
          f"Request to {domain} failed with status code {response.status_code}"
      )

  return {"error": "All fallbacks failed"}


def search_youtube(query):

  for domain in all_domains:
    url = f'https://{domain}/api/v1/search?q={query}'
    response = requests.get(url)

    if response.status_code == 200:
      video_info = response.json()
      video__streams = [
          stream for stream in video_info if stream.get("type") == "video"
      ]
      first_result = video__streams[0]
      youtube_id = first_result.get("videoId")
      print(youtube_id)
      results = get_video_info(youtube_id)
      results["title"] = first_result.get("title")
      return results
    else:
      print(
          f"Request to {domain} failed with status code {response.status_code}"
      )

  return {"error": "All fallbacks failed"}


def parse_search_results(search_results):
  parsed_info_list = []

  for video in search_results:
      if video.get("type") == "video":
          video_id = video.get("videoId")
          if video_id:
              parsed_info = {
                  "stream": f"https://videos.rdwxth.repl.co/api/v1/audio/{encrypt(video_id, key)}?redirect=true",
                  "title": video.get("title", ""),
                  "thumbnail": f"https://videos.rdwxth.repl.co/images/{encrypt(video_id, key)}/thumbnail.png",
              }
              parsed_info_list.append(parsed_info)

  return parsed_info_list

def search_youtube_listed(query):

  for domain in all_domains:
    url = f'https://{domain}/api/v1/search?q={query}'
    response = requests.get(url)

    if response.status_code == 200:
      video_info = response.json()
      video__streams = [
          stream for stream in video_info if stream.get("type") == "video"
      ]


      return parse_search_results(video__streams)
    else:
      print(
          f"Request to {domain} failed with status code {response.status_code}"
      )

  return {"error": "All fallbacks failed"}


def get_playlist_info(playlist_id, page=1):

  for domain in all_domains:
    url = f'https://{domain}/api/v1/playlists/{playlist_id}?page={page}'
  
    try:
        response = requests.get(url)
  
        if response.status_code == 200:
            playlist_info = response.json()
            return parse_playlist_info(playlist_info)
        else:
            print(f"Request to {domain} failed with status code {response.status_code}")
    except Exception as e:
        print(f"An error occurred: {e}")
  
    return {"error": "Failed to get playlist information"}


def parse_playlist_info(playlist_info):
  parsed_info_list = []
  
  for video in playlist_info.get("videos", []):
      video_id = video.get("videoId")
      if video_id:
          parsed_info = {
              "stream": f"https://videos.rdwxth.repl.co/api/v1/audio/{encrypt(video_id, key)}?redirect=true",
              "title": video.get("title", ""),
              "thumbnail": f"https://videos.rdwxth.repl.co/images/{encrypt(video_id, key)}/thumbnail.png",
          }
          parsed_info_list.append(parsed_info)
  
  return parsed_info_list


  
def get_highest_quality_audio(streams):
  # Filter audio streams by MIME type and sort by bitrate in descending order
  audio_streams = [
      stream for stream in streams if stream.get("type").startswith("audio/")
  ]

  # Print debug information
  # print("All streams:", streams)
  # print("Audio streams:", audio_streams)

  sorted_audio_streams = sorted(audio_streams,
                                key=lambda x: int(x.get("bitrate", 0)),
                                reverse=True)

  # Print debug information
  # print("Sorted audio streams:", sorted_audio_streams)

  # Get the highest quality audio stream
  highest_quality_audio = sorted_audio_streams[
      0] if sorted_audio_streams else None

  if highest_quality_audio:
    # Generate a unique UUID hex code
    unique_uuid_hex = str(uuid.uuid4()) + ".mp3"
    # print(highest_quality_audio['url'])
    # Store the URL in the dictionary with the unique UUID hex code as the key
    audio_streams_dict[unique_uuid_hex] = highest_quality_audio['url']

    return {
        "stream": f"https://{request.host}/delivery/{unique_uuid_hex}",
        "status": "Success"
    }
  else:
    return {"status": "No audio streams found"}

@app.route('/api/v2/search', methods=['GET'])
def process_saavn_response():
    q = request.args.get('q')
    if not q:
      abort(400)
      
    # Replace the Saavn API response with the actual response you received
    saavn_response = requests.get(f"https://music-api-pi-tawny.vercel.app/search/all?query={q}").json()



    # Return the modified response
    return jsonify(saavn_response)


@app.route('/api/v2/home', methods=['GET'])
def api_home():
    # Replace the Saavn API response with the actual response you received
    saavn_response = requests.get("https://music-api-pi-tawny.vercel.app/modules?language=english").json()

    # Iterate through albums, playlists, and trending songs to update image URLs
    update_image_urls(saavn_response['data']['albums'])
    update_image_urls(saavn_response['data']['playlists'])
    update_image_urls(saavn_response['data']['trending']['songs'])
    update_image_urls(saavn_response['data']['trending']['albums'])

    # Return the modified response
    return jsonify(saavn_response)

def update_image_urls(items):
    for item in items:
        # Assuming the key for the image is 'image' in each item
        for image in item.get('image', []):
            # Update the 'link' attribute with the new URL format
            image['link'] = f"https://music-api-pi-tawny.vercel.app/covers/{item['name']}/thumbnail.png"



@app.route('/api/v1/audio/<audio_id>', methods=['GET'])
def api_get_video_info(audio_id):
  if request.args.get('redirect') == 'true':
    return redirect(get_video_info(decrypt(audio_id, key))["stream"])
  result = get_video_info(decrypt(audio_id, key))
  return jsonify(result)

@app.route('/api/v1/playlist/<playlist_id>', methods=['GET'])
def api_get_playlist_info(playlist_id):

  result = get_playlist_info(playlist_id)
  return jsonify(result)
  
@app.route('/api/v1/music', methods=['GET'])
def get_music():
  if not request.args.get('q'):
    return jsonify({"error": "No (q)uery provided"})
    
  if request.args.get('redirect') == 'true':
    return redirect(search_youtube(request.args.get('q'))["stream"])
    
  result = search_youtube(f"{request.args.get('q')} official music")
  return jsonify(result)

@app.route('/api/v1/search', methods=['GET'])
def search_music():
  if not request.args.get('q'):
    return jsonify({"error": "No (q)uery provided"})

  result = search_youtube_listed(f"{request.args.get('q')} official music")
  return jsonify(result)



@app.route('/delivery/<string:url>')
def proxy_to_remote_server(url):
  # Replace the URL with the desired destination
  destination_url = audio_streams_dict.get(url)

  # Make a request to the remote server
  response = requests.get(destination_url)

  # Create a Flask response with the same content and headers
  proxied_response = Response(response.content,
                              status=response.status_code,
                              content_type=response.headers['Content-Type'])

  # Copy the headers from the remote server's response to the Flask response
  for header, value in response.headers.items():
    proxied_response.headers[header] = value

  return proxied_response



@app.route('/covers/<string:id>/thumbnail.png')
def proxy_images(id):

  # Make a request to the remote server
  response = requests.get(f"https://img.youtube.com/vi/{id}/maxresdefault.jpg")

  # Create a Flask response with the same content and headers
  proxied_response = Response(response.content,
                              status=response.status_code,
                              content_type=response.headers['Content-Type'])

  # Copy the headers from the remote server's response to the Flask response
  for header, value in response.headers.items():
    proxied_response.headers[header] = value

  return proxied_response

def resize_and_crop(image, size):
    # Resize the image to fit within the specified size while maintaining its aspect ratio
    image.thumbnail(size, Image.ANTIALIAS)

    # Crop the center of the image to achieve the final size
    left = (image.width - size[0]) / 2
    top = (image.height - size[1]) / 2
    right = (image.width + size[0]) / 2
    bottom = (image.height + size[1]) / 2

    return image.crop((left, top, right, bottom))

def search_cover(query):
  resp = requests.get(f"https://saavn.me/search/songs?query={query}&page=1&limit=1").json()
  return resp["data"]["results"][0]["image"][-1]["link"]

@app.route('/covers/<string:name>/thumbnail.png')
def proxy2_images(name):

  # Make a request to the remote server
  response = requests.get(search_cover(name))

  # Create a Flask response with the same content and headers
  proxied_response = Response(response.content,
                              status=response.status_code,
                              content_type=response.headers['Content-Type'])

  # Copy the headers from the remote server's response to the Flask response
  for header, value in response.headers.items():
    proxied_response.headers[header] = value

  return proxied_response



@app.errorhandler(Exception)
def error_handler(e):
    return jsonify({"error": str(e)}), 500

@app.route('/test', methods=['GET'])
def test():
  return render_template("index.html")


if __name__ == '__main__':
  app.run(host="0.0.0.0", port=8080)
