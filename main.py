import asyncio
from yandex_music import ClientAsync
from yandex_music.exceptions import NotFoundError
import aiohttp
import colorgram
from io import BytesIO
from dotenv import load_dotenv
import os
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
            "full_name": self.full_name
        }
    
    # metod get liked track(only this, track_id<-number in playlist )
    async def getLikedTrack(self, track_id=None) -> dict:
        likedTrack = await self.client.users_likes_tracks()
        fetchTrack = await likedTrack[track_id].fetch_track_async()
        return fetchTrack
        
    # metod get link for play track
    async def getInfoDownloadTrack(self, track_id=None) -> dict:
        trackInfo = await self.client.tracks_download_info(track_id=track_id, get_direct_links=True)
        return trackInfo[-1]
    
    # metod get info about track (title, avatarTrack, artist, avatarArtist)
    async def getInfoTrack(self, track_id=None) -> dict:
        info = (await self.client.tracks([track_id]))[0]
        artist = info.artists
        
        return {
            "title": info.title,
            "avatarTrack": f"https://{info.cover_uri[:-2]}400x400", 
            "artist": artist[0].name,
            "avatarArtist": f"https://{artist[0].cover.uri[:-2]}200x200"
        }

    # metod get dominant color
    async def getTrackColor(self, track_id=None) -> str | None:
      
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
    async def DownloadTrack(self, track_id=None) -> bool:
        try:
            downloadInfo = await self.getInfoDownloadTrack(track_id)
            await downloadInfo.download_async('rr.mp3')
            return True
        except NotFoundError:
            print('Track not found')
            return False
   
    async def LikeTrack(self, track_id=None, user_id=None) -> bool:
        return await self.client.users_likes_tracks_add(track_ids=track_id, user_id=user_id)
    
    async def DislikeTrack(self, track_id=None, user_id=None) -> bool:
        return await self.client.users_likes_tracks_remove(track_ids=track_id, user_id=user_id)
         
    
# class for work with "my wawe"
class MyWaweClient(MainResponse):

    def __init__(self, token):
        super().__init__(token)
    
    # function for change settings "My wawe" 
    # mood_energy (`mood_energy`: `fun`, `active`, `calm`, `sad`, `all`.)
    # diverdity (`favorite`, `popular`, `discover`, `default`)
    # language (`russian`, `not-russian`, `any`)
    # type_ (`rotor`, `generative`)
    async def changeSettingsWawe(self, mood_energy='all', diversity='default', language='any', type_='rotor') -> bool:
        access = await self.client.rotor_station_settings2( station='user:onyourwave',
            mood_energy=mood_energy, 
            diversity=diversity,
            language=language,  
            type_=type_ )
        return access
    
    # medod get track from "my wawe"
    async def getMyWawe(self, mood_energy='all', diversity='default', language='any', type_='rotor'):
        await self.changeSettingsWawe(mood_energy, diversity, language, type_)
        tracksWawe = await self.client.rotor_station_tracks(station='user:onyourwave', settings2=True)

        return tracksWawe

   
async def main():
    token = os.getenv('TOKEN')
    main_response = await MainResponse(token).init()
    uid = await main_response.getAccountInfo()
    uid = uid['uid']
    print(uid)
    info = await main_response.LikeAndDislikeTrack(track_id=66190680, user_id=uid)
    print(info)

    
    # wawe = await MyWaweClient(token).init()
    # tracks = await wawe.getMyWawe()
    # print(tracks.sequence)
    



if __name__ == '__main__':
    asyncio.run(main())



# p = MainResponse('y0_AgAAAABldaDNAAG8XgAAAAEKnK0JAAB7iUrEOw9H6qRMzmG_4LpBOeaz-w')
# # Пример использования нового метода
# track_id_to_check = 66190680
# # print(p.getInfoTrack(track_id_to_check))
# color = p.getTrackColor(track_id_to_check)
# if color:
#     print(f"Доминирующий цвет трека {track_id_to_check}: {color}")

# o = MyWaweClient('y0_AgAAAABldaDNAAG8XgAAAAEKnK0JAAB7iUrEOw9H6qRMzmG_4LpBOeaz-w')
# print(o.changeSettingsWawe(mood_energy='active', diversity='default', language='russian', type_='rotor'))
# print(o.getMyWawe().sequence[0])