from fastapi import FastAPI, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional, Union
from pydantic import BaseModel
import os
from main import MainResponse, MyWaveClient


app = FastAPI()

origins = [
    "http://localhost:1420",  # твой Tauri UI
    "http://127.0.0.1:1420",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,            # откуда можно делать запросы
    allow_credentials=True,
    allow_methods=["*"],              # какие методы разрешены (GET, POST и т.д.)
    allow_headers=["*"],              # какие заголовки разрешены
)

# ✅ 1. Модель для getAccountInfo
class AccountInfo(BaseModel):
    uid: int
    login: str
    full_name: str


# ✅ 2. Модели для getLikedTrack
class Artist(BaseModel):
    id: str
    name: str


class Album(BaseModel):
    id: str
    title: str


class LikedTrack(BaseModel):
    id: str
    title: str
    artists: List[Artist]
    albums: List[Album]


# ✅ 3. Модель для isTrackLiked
class TrackLikedStatus(BaseModel):
    track_id: str
    is_liked: bool


# ✅ 4. Модель для getInfoDownloadTrack
class DownloadInfo(BaseModel):
    codec: str
    bitrate_in_kbps: int
    download_url: str


# ✅ 5. Модель для getInfoTrack
class TrackInfo(BaseModel):
    title: str
    avatarTrack: str
    artist: str
    avatarArtist: str


# ✅ 6. Модель для getTrackColor
class DominantColor(BaseModel):
    color_hex: str


# ✅ 7. Модель для DownloadTrack
class DownloadResponse(BaseModel):
    success: bool


# ✅ 8. Модель для LikeAndDislikeTrack
class LikeToggleResponse(BaseModel):
    success: bool


# ✅ 9. Модель для HateTrack
class HateTrackResponse(BaseModel):
    success: bool


# ✅ 10. Модели для getMyWave
class WaveTrack(BaseModel):
    track_id: str
    title: str
    liked: bool
    name: str
    avatar: str
    imgAlbum: str


class WaveBatchInfo(BaseModel):
    batch_id: str


# ✅ 11. Общая модель для Feedback методов
class FeedbackResponse(BaseModel):
    success: bool
    detail: Optional[str] = None




# Dependency: получить и инициализировать клиента
async def get_client() -> MainResponse:
    token = os.getenv('TOKEN')
    client = await MainResponse(token).init()
    return client

async def get_wave_client() -> MyWaveClient:
    token = os.getenv('TOKEN')
    client = await MyWaveClient(token).init()
    return client


@app.get("/account", response_model=AccountInfo)
async def get_account_info(client: MainResponse = Depends(get_client)):
    return await client.getAccountInfo()


@app.get("/liked-track/{track_id}", response_model=LikedTrack)
async def get_liked_track(track_id: int, client: MainResponse = Depends(get_client)):
    return await client.getLikedTrack(track_id)


@app.get("/is-liked/{track_id}", response_model=TrackLikedStatus)
async def is_track_liked(track_id: Union[str, int], client: MainResponse = Depends(get_client)):
    is_liked = await client.isTrackLiked(track_id)
    return {"track_id": str(track_id), "is_liked": is_liked}


@app.get("/download-info/{track_id}", response_model=list[DownloadInfo])
async def get_download_info(track_id: Union[str, int], client: MainResponse = Depends(get_client)):
    return await client.getInfoDownloadTrack(track_id)


@app.get("/track-info/{track_id}", response_model=TrackInfo)
async def get_track_info(track_id: Union[str, int], client: MainResponse = Depends(get_client)):
    return await client.getInfoTrack(track_id)


@app.get("/track-color/{track_id}", response_model=DominantColor)
async def get_track_color(track_id: Union[str, int], client: MainResponse = Depends(get_client)):
    color = await client.getTrackColor(track_id)
    return {"color_hex": color or "#000000"}


@app.post("/download/{track_id}", response_model=DownloadResponse)
async def download_track(track_id: Union[str, int], client: MainResponse = Depends(get_client)):
    success = await client.DownloadTrack(track_id)
    return {"success": success}


@app.post("/like-toggle/{track_id}", response_model=LikeToggleResponse)
async def toggle_like(track_id: Union[str, int], client: MainResponse = Depends(get_client)):
    result = await client.LikeAndDislikeTrack(track_id)
    return {"success": result is True}


@app.post("/hate/{track_id}", response_model=HateTrackResponse)
async def hate_track(track_id: Union[str, int], client: MainResponse = Depends(get_client)):
    result = await client.HateTrack(track_id)
    return {"success": result is True}


@app.get("/wave", response_model=list[Union[WaveTrack, WaveBatchInfo]])
async def get_my_wave(
    mood_energy: str = Query(default="all"),
    diversity: str = Query(default="default"),
    language: str = Query(default="any"),
    type_: str = Query(default="generative"),
    queue: Optional[str] = None,
    client: MyWaveClient = Depends(get_wave_client)
):
    return await client.getMyWave(mood_energy, diversity, language, type_, queue)


@app.post("/feedback/radio-start", response_model=FeedbackResponse)
async def feedback_radio_start(batch_id: str, client: MyWaveClient = Depends(get_wave_client)):
    try:
        await client.TrackFeedBackRadioStarted(batch_id)
        return {"success": True}
    except Exception as e:
        return {"success": False, "detail": str(e)}


@app.post("/feedback/track-start", response_model=FeedbackResponse)
async def feedback_track_start(track_id: str, batch_id: str, client: MyWaveClient = Depends(get_wave_client)):
    try:
        await client.TrackFeedBackTrackStarted(track_id, batch_id)
        return {"success": True}
    except Exception as e:
        return {"success": False, "detail": str(e)}


@app.post("/feedback/track-finish", response_model=FeedbackResponse)
async def feedback_track_finish(track_id: str, batch_id: str, total_played_seconds: Optional[int] = None, client: MyWaveClient = Depends(get_wave_client)):
    try:
        await client.TrackFeedBackTrackFinished(track_id, batch_id, total_played_seconds)
        return {"success": True}
    except Exception as e:
        return {"success": False, "detail": str(e)}


@app.post("/feedback/track-skip", response_model=FeedbackResponse)
async def feedback_track_skip(track_id: str, batch_id: str, total_played_seconds: int, client: MyWaveClient = Depends(get_wave_client)):
    try:
        await client.TrackFeedBackTrackSkipped(track_id, total_played_seconds, batch_id)
        return {"success": True}
    except Exception as e:
        return {"success": False, "detail": str(e)}
