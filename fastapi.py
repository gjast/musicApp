from fastapi import FastAPI, Depends
from pydantic import BaseModel

from typing import List, Optional
app = FastAPI()





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


# ✅ 10. Модели для getMyWawe
class WaweTrack(BaseModel):
    track_id: str
    title: str
    liked: bool
    name: str
    avatar: str
    imgAlbum: str


class WaweBatchInfo(BaseModel):
    batch_id: str


# ✅ 11. Общая модель для Feedback методов
class FeedbackResponse(BaseModel):
    success: bool
    detail: Optional[str] = None
