import asyncio
from yandex_music import ClientAsync
from yandex_music.exceptions import NotFoundError
import aiohttp
import colorgram
from io import BytesIO
from dotenv import load_dotenv
import os
from datetime import datetime

load_dotenv()

class MainResponse:
    #constructor
    def __init__(self, token):
        self.token = token
        self.client = None
        self.uid = None
        self.login = None
        self.full_name = None

    # init client
    async def init(self):
        self.client = await ClientAsync(self.token).init()
        return self

    # metod get info about account (uid, login, full_name)
    async def getAccountInfo(self) -> dict:
        accountStatus = await self.client.account_status()

        self.uid = accountStatus.account.uid
        self.login = accountStatus.account.login
        self.full_name = accountStatus.account.full_name

        return {
            "uid": self.uid,
            "login": self.login,
            "full_name": self.full_name,
        }
    
    # metod get liked track(only this, track_id<-number in playlist )
    async def getLikedTrack(self, track_id: int) -> dict:
        likedTrack = await self.client.users_likes_tracks()
        fetchTrack = await likedTrack[track_id].fetch_track_async()
        return fetchTrack

    # medod check liked track
    async def isTrackLiked(self, track_id: str | int) -> bool:
            liked = (await self.client.users_likes_tracks()).tracks
            return any(track.id == str(track_id) for track in liked)

    # metod get link for play track
    async def getInfoDownloadTrack(self, track_id: str | int) -> dict:
        trackInfo = (await self.client.tracks_download_info(track_id=track_id, get_direct_links=True))
        return [x for x in trackInfo if x['bitrate_in_kbps'] == 320]
    
    # metod get info about track (title, avatarTrack, artist, avatarArtist)
    async def getInfoTrack(self, track_id: str | int) -> dict:
        info = (await self.client.tracks([track_id]))[0]
        artist = info.artists
        
        
        return {
            # "all" : info,
            # "like": info.like,
            "title": info.title,
            "avatarTrack": f"https://{info.cover_uri[:-2]}400x400", 
            "artist": artist[0].name,
            "avatarArtist": f"https://{artist[0].cover.uri[:-2]}200x200"
        }

    # metod get dominant color
    async def getTrackColor(self, track_id: str | int) -> str | None:
      
        track_info = await self.getInfoTrack(track_id)  # обязательно await
        cover_url = track_info.get("avatarTrack")

        if not cover_url:
            print("Cover URL not found.")
            return None

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(cover_url) as response:
                    if response.status != 200:
                        print(f"Ошибка при загрузке изображения: {response.status}")
                        return None

                    img_bytes = await response.read()
                    img_stream = BytesIO(img_bytes)

                # Извлекаем 1 самый доминирующий цвет
                    colors = colorgram.extract(img_stream, 1)

                    if colors:
                        dominant_color = colors[0].rgb
                        return f"#{dominant_color.r:02x}{dominant_color.g:02x}{dominant_color.b:02x}"
                    else:
                        return None

        except Exception as e:
            print(f"Произошла ошибка при извлечении цвета: {e}")
            return None
        
    # metod download track
    async def DownloadTrack(self, track_id: str | int) -> bool:
        try:
            downloadInfo = await self.getInfoDownloadTrack(track_id)
            await downloadInfo.download_async('rr.mp3')
            return True
        except NotFoundError:
            print('Track not found')
            return False
   
   #metod LikeAndDislikeTrack (add or remove track from playlist "favorites")
    async def LikeAndDislikeTrack(self, track_id: str | int, user_id=None) -> bool:
        try:
            is_liked = await self.isTrackLiked(track_id)

            if is_liked:
                await self.client.users_likes_tracks_remove(track_ids=track_id, user_id=user_id)
            else:
                await self.client.users_likes_tracks_add(track_ids=track_id, user_id=user_id)

            return True

        except Exception as e:
            return e
         
    #metod add hate track      
    async def HateTrack(self, track_id: str | int):
        try:
            await self.client.users_dislikes_tracks_add(track_ids=track_id)
            return True
        except Exception as e:
            return e
    




# class for work with "my wawe"
class MyWaweClient(MainResponse):

    def __init__(self, token):
        super().__init__(token)
    
    # function for change settings "My wawe" 
    # mood_energy (`mood_energy`: `fun`, `active`, `calm`, `sad`, `all`.)
    # diverdity (`favorite`, `popular`, `discover`, `default`)
    # language (`russian`, `not-russian`, `any`)
    # type_ (`rotor`, `generative`)
    async def changeSettingsWawe(self, mood_energy='all', diversity='default', language='any', type_='generative') -> bool:
        access = await self.client.rotor_station_settings2( station='user:onyourwave',
            mood_energy=mood_energy, 
            diversity=diversity,
            language=language,  
            type_=type_ )
        return access
    
    # medod get track from "my wawe"
    async def getMyWawe(self, mood_energy='all', diversity='default', language='any', type_='generative', queue=None):

        await self.changeSettingsWawe(mood_energy, diversity, language, type_)

        tracksWawe = await self.client.rotor_station_tracks(station='user:onyourwave', settings2=True, queue=queue)

        return [
            {
                "track_id": item.track.id,
                "title": item.track.title,
                "liked": item.liked,
                "name": item.track.artists[0].name,
                "avatar": f'https://{item.track.artists[0].cover.uri[:-2]}800x800',
                "imgAlbum": f'https://{item.track.albums[0].cover_uri[:-2]}800x800'
            }
            for item in tracksWawe.sequence
        ] + [
            {
                "batch_id": tracksWawe.batch_id
            }
        ]

    

    async def TrackFeedBackRadioStarted(self, batch_id):
        try:
            return await self.client.rotor_station_feedback_radio_started(station="user:onyourwave", from_=None, batch_id=batch_id, timestamp=datetime.now().timestamp())
        except Exception as e:
            return e
       
    async def TrackFeedBackTrackStarted(self, track_id, batch_id):
        try:
            return await self.client.rotor_station_feedback_radio_stopped(station="user:onyourwave", track_id=track_id, batch_id=batch_id, timestamp=datetime.now().timestamp())
        except Exception as e:
            return e

    async def TrackFeedBackTrackFinished(self, track_id, batch_id, total_played_seconds=None):
        try:
            return await self.client.rotor_station_feedback_track_finished(station="user:onyourwave", track_id=track_id,  total_played_seconds=total_played_seconds, batch_id=batch_id, timestamp=datetime.now().timestamp())
        except Exception as e:
            return e

    async def TrackFeedBackTrackSkipped(self, track_id, total_played_seconds, batch_id):
        try:
            return await self.client.rotor_station_feedback_track_skip(station="user:onyourwave", track_id=track_id, total_played_seconds=total_played_seconds, batch_id=batch_id, timestamp=datetime.now().timestamp())
        except Exception as e:
            return e




import os
import asyncio
from datetime import datetime

async def main():
    token = os.getenv('TOKEN')
    wawe = await MyWaweClient(token).init()
    print(await wawe.getMyWawe())
    #133025331
    # ma = await MainResponse(token).init()
    # print(await ma.getInfoDownloadTrack(133025331))

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
