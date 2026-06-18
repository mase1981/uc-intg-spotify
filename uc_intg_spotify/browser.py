"""Spotify media browser. :copyright: (c) 2024 by Meir Miyara. :license: MPL-2.0"""
from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

from ucapi import StatusCodes
from ucapi.api_definitions import Pagination
from ucapi.media_player import (
    BrowseMediaItem,
    BrowseOptions,
    BrowseResults,
    MediaClass,
    MediaContentType,
    SearchOptions,
    SearchResults,
)

if TYPE_CHECKING:
    from uc_intg_spotify.client import SpotifyClient

_LOG = logging.getLogger(__name__)

ROOT_ITEMS = [
    ("playlists", "Playlists", MediaClass.PLAYLIST),
    ("saved_tracks", "Liked Songs", MediaClass.TRACK),
    ("saved_albums", "Albums", MediaClass.ALBUM),
    ("recently_played", "Recently Played", MediaClass.TRACK),
    ("top_tracks", "Top Tracks", MediaClass.TRACK),
    ("top_artists", "Top Artists", MediaClass.ARTIST),
    ("followed_artists", "Artists", MediaClass.ARTIST),
    ("new_releases", "New Releases", MediaClass.ALBUM),
    ("queue", "Queue", MediaClass.TRACK),
]


async def browse(client: SpotifyClient, options: BrowseOptions) -> BrowseResults | StatusCodes:
    if not client or not client.is_authenticated():
        return StatusCodes.SERVICE_UNAVAILABLE

    media_id = options.media_id if hasattr(options, "media_id") else None

    if not media_id or media_id == "root":
        return await _browse_root(client)

    if media_id == "playlists":
        return await _browse_playlists(client, options)

    if media_id == "saved_tracks":
        return await _browse_saved_tracks(client, options)

    if media_id == "saved_albums":
        return await _browse_saved_albums(client, options)

    if media_id == "recently_played":
        return await _browse_recently_played(client, options)

    if media_id == "top_tracks":
        return await _browse_top_tracks(client, options)

    if media_id == "top_artists":
        return await _browse_top_artists(client, options)

    if media_id == "followed_artists":
        return await _browse_followed_artists(client, options)

    if media_id == "new_releases":
        return await _browse_new_releases(client, options)

    if media_id == "queue":
        return await _browse_queue(client, options)

    if media_id.startswith("playlist_"):
        playlist_id = media_id[9:]
        return await _browse_playlist_tracks(client, playlist_id, options)

    if media_id.startswith("album_"):
        album_id = media_id[6:]
        return await _browse_album_tracks(client, album_id, options)

    if media_id.startswith("artist_"):
        artist_id = media_id[7:]
        return await _browse_artist(client, artist_id, options)

    return StatusCodes.NOT_FOUND


async def search(client: SpotifyClient, options: SearchOptions) -> SearchResults | StatusCodes:
    if not client or not client.is_authenticated():
        return StatusCodes.SERVICE_UNAVAILABLE

    query = options.query if hasattr(options, "query") else ""
    if not query:
        return SearchResults(media=[], pagination=Pagination(page=1, limit=0, count=0))

    page = _get_page(options)
    limit = _get_limit(options, default=20)
    offset = (page - 1) * limit

    data = await client.search(query, limit=limit, offset=offset)
    if not data:
        return SearchResults(media=[], pagination=Pagination(page=1, limit=0, count=0))

    results = []

    for track in data.get("tracks", {}).get("items", []):
        item = _track_to_browse_item(track)
        if item:
            results.append(item)

    for album in data.get("albums", {}).get("items", []):
        item = _album_to_browse_item(album)
        if item:
            results.append(item)

    for artist in data.get("artists", {}).get("items", []):
        item = _artist_to_browse_item(artist)
        if item:
            results.append(item)

    for playlist in data.get("playlists", {}).get("items", []):
        item = _playlist_to_browse_item(playlist)
        if item:
            results.append(item)

    total = sum(
        data.get(k, {}).get("total", 0) for k in ("tracks", "albums", "artists", "playlists")
    )

    return SearchResults(
        media=results,
        pagination=Pagination(page=page, limit=limit, count=total),
    )


async def _browse_root(client: SpotifyClient) -> BrowseResults:
    thumbnails = await _fetch_root_thumbnails(client)

    items = []
    for item_id, title, media_class in ROOT_ITEMS:
        items.append(BrowseMediaItem(
            title=title,
            media_class=media_class,
            media_type="directory",
            media_id=item_id,
            can_browse=True,
            can_play=False,
            thumbnail=thumbnails.get(item_id),
        ))

    return BrowseResults(
        media=BrowseMediaItem(
            title="Spotify",
            media_class=MediaClass.DIRECTORY,
            media_type="root",
            media_id="root",
            can_browse=True,
            can_search=True,
            items=items,
        ),
        pagination=Pagination(page=1, limit=len(items), count=len(items)),
    )


async def _fetch_root_thumbnails(client: SpotifyClient) -> dict[str, str | None]:
    async def _first_image(coro, *keys) -> tuple[str, str | None]:
        try:
            data = await coro
            if not data:
                return keys[0], None
            obj = data
            for k in keys[1:]:
                obj = obj.get(k, {}) if isinstance(obj, dict) else {}
            items = obj.get("items", []) if isinstance(obj, dict) else obj
            if isinstance(items, list):
                for item in items:
                    track = item.get("track", item) if isinstance(item, dict) else item
                    if isinstance(track, dict):
                        images = track.get("images") or track.get("album", {}).get("images", [])
                        if images:
                            return keys[0], images[0].get("url")
        except Exception:
            pass
        return keys[0], None

    results = await asyncio.gather(
        _first_image(client.get_user_playlists(limit=1, offset=0), "playlists"),
        _first_image(client.get_saved_tracks(limit=1, offset=0), "saved_tracks"),
        _first_image(client.get_saved_albums(limit=1, offset=0), "saved_albums"),
        _first_image(client.get_recently_played(limit=1), "recently_played"),
        _first_image(client.get_top_tracks(limit=1, offset=0), "top_tracks"),
        _first_image(client.get_top_artists(limit=1, offset=0), "top_artists"),
        _first_image(client.get_followed_artists(limit=1), "followed_artists", "artists"),
        _first_image(client.get_new_releases(limit=1, offset=0), "new_releases", "albums"),
        return_exceptions=True,
    )

    thumbnails: dict[str, str | None] = {}
    for result in results:
        if isinstance(result, tuple):
            thumbnails[result[0]] = result[1]
    return thumbnails


async def _browse_playlists(client: SpotifyClient, options: BrowseOptions) -> BrowseResults:
    page = _get_page(options)
    limit = _get_limit(options)
    offset = (page - 1) * limit

    data = await client.get_user_playlists(limit=limit, offset=offset)
    if not data:
        return _empty_browse("playlists", "Playlists", page, limit)

    items = []
    for playlist in data.get("items", []):
        item = _playlist_to_browse_item(playlist)
        if item:
            items.append(item)

    total = data.get("total", 0)
    return BrowseResults(
        media=BrowseMediaItem(
            title="Playlists",
            media_class=MediaClass.PLAYLIST,
            media_type="directory",
            media_id="playlists",
            can_browse=True,
            can_search=True,
            items=items,
        ),
        pagination=Pagination(page=page, limit=limit, count=total),
    )


async def _browse_saved_tracks(client: SpotifyClient, options: BrowseOptions) -> BrowseResults:
    page = _get_page(options)
    limit = _get_limit(options)
    offset = (page - 1) * limit

    data = await client.get_saved_tracks(limit=limit, offset=offset)
    if not data:
        return _empty_browse("saved_tracks", "Liked Songs", page, limit)

    items = []
    for saved in data.get("items", []):
        track = saved.get("track")
        if track:
            item = _track_to_browse_item(track)
            if item:
                items.append(item)

    total = data.get("total", 0)
    return BrowseResults(
        media=BrowseMediaItem(
            title="Liked Songs",
            media_class=MediaClass.TRACK,
            media_type="directory",
            media_id="saved_tracks",
            can_browse=True,
            items=items,
        ),
        pagination=Pagination(page=page, limit=limit, count=total),
    )


async def _browse_saved_albums(client: SpotifyClient, options: BrowseOptions) -> BrowseResults:
    page = _get_page(options)
    limit = _get_limit(options)
    offset = (page - 1) * limit

    data = await client.get_saved_albums(limit=limit, offset=offset)
    if not data:
        return _empty_browse("saved_albums", "Albums", page, limit)

    items = []
    for saved in data.get("items", []):
        album = saved.get("album")
        if album:
            item = _album_to_browse_item(album)
            if item:
                items.append(item)

    total = data.get("total", 0)
    return BrowseResults(
        media=BrowseMediaItem(
            title="Albums",
            media_class=MediaClass.ALBUM,
            media_type="directory",
            media_id="saved_albums",
            can_browse=True,
            items=items,
        ),
        pagination=Pagination(page=page, limit=limit, count=total),
    )


async def _browse_recently_played(client: SpotifyClient, options: BrowseOptions) -> BrowseResults:
    limit = _get_limit(options)

    data = await client.get_recently_played(limit=limit)
    if not data:
        return _empty_browse("recently_played", "Recently Played", 1, limit)

    items = []
    for entry in data.get("items", []):
        track = entry.get("track")
        if track:
            item = _track_to_browse_item(track)
            if item:
                items.append(item)

    return BrowseResults(
        media=BrowseMediaItem(
            title="Recently Played",
            media_class=MediaClass.TRACK,
            media_type="directory",
            media_id="recently_played",
            can_browse=True,
            items=items,
        ),
        pagination=Pagination(page=1, limit=len(items), count=len(items)),
    )


async def _browse_top_tracks(client: SpotifyClient, options: BrowseOptions) -> BrowseResults:
    page = _get_page(options)
    limit = _get_limit(options)
    offset = (page - 1) * limit

    data = await client.get_top_tracks(limit=limit, offset=offset)
    if not data:
        return _empty_browse("top_tracks", "Top Tracks", page, limit)

    items = []
    for track in data.get("items", []):
        item = _track_to_browse_item(track)
        if item:
            items.append(item)

    total = data.get("total", 0)
    return BrowseResults(
        media=BrowseMediaItem(
            title="Top Tracks",
            media_class=MediaClass.TRACK,
            media_type="directory",
            media_id="top_tracks",
            can_browse=True,
            items=items,
        ),
        pagination=Pagination(page=page, limit=limit, count=total),
    )


async def _browse_top_artists(client: SpotifyClient, options: BrowseOptions) -> BrowseResults:
    page = _get_page(options)
    limit = _get_limit(options)
    offset = (page - 1) * limit

    data = await client.get_top_artists(limit=limit, offset=offset)
    if not data:
        return _empty_browse("top_artists", "Top Artists", page, limit)

    items = []
    for artist in data.get("items", []):
        item = _artist_to_browse_item(artist)
        if item:
            items.append(item)

    total = data.get("total", 0)
    return BrowseResults(
        media=BrowseMediaItem(
            title="Top Artists",
            media_class=MediaClass.ARTIST,
            media_type="directory",
            media_id="top_artists",
            can_browse=True,
            items=items,
        ),
        pagination=Pagination(page=page, limit=limit, count=total),
    )


async def _browse_followed_artists(client: SpotifyClient, options: BrowseOptions) -> BrowseResults:
    limit = _get_limit(options)

    data = await client.get_followed_artists(limit=limit)
    if not data:
        return _empty_browse("followed_artists", "Artists", 1, limit)

    artists_data = data.get("artists", {})
    items = []
    for artist in artists_data.get("items", []):
        item = _artist_to_browse_item(artist)
        if item:
            items.append(item)

    total = artists_data.get("total", len(items))
    return BrowseResults(
        media=BrowseMediaItem(
            title="Artists",
            media_class=MediaClass.ARTIST,
            media_type="directory",
            media_id="followed_artists",
            can_browse=True,
            items=items,
        ),
        pagination=Pagination(page=1, limit=len(items), count=total),
    )


async def _browse_new_releases(client: SpotifyClient, options: BrowseOptions) -> BrowseResults:
    page = _get_page(options)
    limit = _get_limit(options, default=20)
    offset = (page - 1) * limit

    data = await client.get_new_releases(limit=limit, offset=offset)
    if not data:
        return _empty_browse("new_releases", "New Releases", page, limit)

    items = []
    for album in data.get("albums", {}).get("items", []):
        item = _album_to_browse_item(album)
        if item:
            items.append(item)

    total = data.get("albums", {}).get("total", 0)
    return BrowseResults(
        media=BrowseMediaItem(
            title="New Releases",
            media_class=MediaClass.ALBUM,
            media_type="directory",
            media_id="new_releases",
            can_browse=True,
            items=items,
        ),
        pagination=Pagination(page=page, limit=limit, count=total),
    )


async def _browse_queue(client: SpotifyClient, options: BrowseOptions) -> BrowseResults:
    data = await client.get_queue()
    if not data:
        return _empty_browse("queue", "Queue", 1, 50)

    items = []
    current = data.get("currently_playing")
    if current and current.get("type") == "track":
        item = _track_to_browse_item(current)
        if item:
            item = BrowseMediaItem(
                title=f"Now: {item.title}",
                media_class=item.media_class,
                media_type=item.media_type,
                media_id=item.media_id,
                can_browse=False,
                can_play=True,
                thumbnail=item.thumbnail,
                artist=item.artist,
                album=item.album,
                duration=item.duration,
            )
            items.append(item)

    for track in data.get("queue", []):
        if track.get("type") == "track":
            item = _track_to_browse_item(track)
            if item:
                items.append(item)

    return BrowseResults(
        media=BrowseMediaItem(
            title="Queue",
            media_class=MediaClass.TRACK,
            media_type="directory",
            media_id="queue",
            can_browse=True,
            items=items,
        ),
        pagination=Pagination(page=1, limit=len(items), count=len(items)),
    )


async def _browse_playlist_tracks(
    client: SpotifyClient, playlist_id: str, options: BrowseOptions
) -> BrowseResults:
    data = await client.get_playlist(playlist_id)
    if not data:
        return _empty_browse(f"playlist_{playlist_id}", "Playlist", 1, 50)

    playlist_name = data.get("name", "Playlist")
    playlist_images = data.get("images", [])
    playlist_thumbnail = playlist_images[0]["url"] if playlist_images else None

    tracks_data = data.get("tracks") or data.get("items") or {}
    items = []
    for item_data in tracks_data.get("items", []):
        track = item_data.get("track")
        if track and track.get("type") == "track":
            item = _track_to_browse_item(track)
            if item:
                items.append(item)

    total = tracks_data.get("total", len(items))
    return BrowseResults(
        media=BrowseMediaItem(
            title=playlist_name,
            media_class=MediaClass.PLAYLIST,
            media_type="playlist",
            media_id=f"playlist_{playlist_id}",
            can_browse=True,
            can_play=True,
            thumbnail=playlist_thumbnail,
            items=items,
        ),
        pagination=Pagination(page=1, limit=total, count=total),
    )


async def _browse_album_tracks(
    client: SpotifyClient, album_id: str, options: BrowseOptions
) -> BrowseResults:
    data = await client.get_album(album_id)
    if not data:
        return _empty_browse(f"album_{album_id}", "Album", 1, 50)

    album_name = data.get("name", "Album")
    album_images = data.get("images", [])
    album_thumbnail = album_images[0]["url"] if album_images else None
    album_artists = ", ".join(a.get("name", "") for a in data.get("artists", []))

    tracks_data = data.get("tracks", {})
    items = []
    for track in tracks_data.get("items", []):
        track_id = track.get("id", "")
        track_name = track.get("name", "")
        track_num = track.get("track_number", 0)
        duration_ms = track.get("duration_ms", 0)

        if not track_id or not track_name:
            continue

        title = f"{track_num}. {track_name}" if track_num else track_name

        items.append(BrowseMediaItem(
            title=title,
            media_class=MediaClass.TRACK,
            media_type=MediaContentType.TRACK,
            media_id=f"track_{track_id}",
            can_browse=False,
            can_play=True,
            thumbnail=album_thumbnail,
            artist=album_artists,
            album=album_name,
            duration=duration_ms // 1000,
        ))

    total = tracks_data.get("total", len(items))
    return BrowseResults(
        media=BrowseMediaItem(
            title=album_name,
            media_class=MediaClass.ALBUM,
            media_type="album",
            media_id=f"album_{album_id}",
            can_browse=True,
            can_play=True,
            thumbnail=album_thumbnail,
            items=items,
        ),
        pagination=Pagination(page=1, limit=total, count=total),
    )


async def _browse_artist(
    client: SpotifyClient, artist_id: str, options: BrowseOptions
) -> BrowseResults:
    artist_data = await client.get_artist(artist_id)
    if not artist_data:
        return _empty_browse(f"artist_{artist_id}", "Artist", 1, 50)

    artist_name = artist_data.get("name", "Artist")
    artist_images = artist_data.get("images", [])
    artist_thumbnail = artist_images[0]["url"] if artist_images else None

    items = []

    top_tracks = await client.get_artist_top_tracks(artist_id)
    if top_tracks:
        for track in top_tracks.get("tracks", []):
            item = _track_to_browse_item(track)
            if item:
                items.append(item)

    albums = await client.get_artist_albums(artist_id, limit=20)
    if albums:
        for album in albums.get("items", []):
            item = _album_to_browse_item(album)
            if item:
                items.append(item)

    return BrowseResults(
        media=BrowseMediaItem(
            title=artist_name,
            media_class=MediaClass.ARTIST,
            media_type="artist",
            media_id=f"artist_{artist_id}",
            can_browse=True,
            thumbnail=artist_thumbnail,
            items=items,
        ),
        pagination=Pagination(page=1, limit=len(items), count=len(items)),
    )


def _track_to_browse_item(track: dict) -> BrowseMediaItem | None:
    track_id = track.get("id", "")
    track_name = track.get("name", "")
    if not track_id or not track_name:
        return None

    artists = ", ".join(a.get("name", "") for a in track.get("artists", []))
    album = track.get("album", {})
    album_name = album.get("name", "")
    images = album.get("images", [])
    thumbnail = images[0]["url"] if images else None
    duration_ms = track.get("duration_ms", 0)

    return BrowseMediaItem(
        title=track_name,
        media_class=MediaClass.TRACK,
        media_type=MediaContentType.TRACK,
        media_id=f"track_{track_id}",
        can_browse=False,
        can_play=True,
        thumbnail=thumbnail,
        artist=artists,
        album=album_name,
        duration=duration_ms // 1000,
    )


def _album_to_browse_item(album: dict) -> BrowseMediaItem | None:
    album_id = album.get("id", "")
    album_name = album.get("name", "")
    if not album_id or not album_name:
        return None

    artists = ", ".join(a.get("name", "") for a in album.get("artists", []))
    images = album.get("images", [])
    thumbnail = images[0]["url"] if images else None

    return BrowseMediaItem(
        title=album_name,
        media_class=MediaClass.ALBUM,
        media_type=MediaContentType.ALBUM,
        media_id=f"album_{album_id}",
        can_browse=True,
        can_play=True,
        thumbnail=thumbnail,
        artist=artists,
    )


def _artist_to_browse_item(artist: dict) -> BrowseMediaItem | None:
    artist_id = artist.get("id", "")
    artist_name = artist.get("name", "")
    if not artist_id or not artist_name:
        return None

    images = artist.get("images", [])
    thumbnail = images[0]["url"] if images else None

    return BrowseMediaItem(
        title=artist_name,
        media_class=MediaClass.ARTIST,
        media_type=MediaContentType.ARTIST,
        media_id=f"artist_{artist_id}",
        can_browse=True,
        can_play=False,
        thumbnail=thumbnail,
    )


def _playlist_to_browse_item(playlist: dict) -> BrowseMediaItem | None:
    if not playlist:
        return None
    playlist_id = playlist.get("id", "")
    playlist_name = playlist.get("name", "")
    if not playlist_id or not playlist_name:
        return None

    images = playlist.get("images", [])
    thumbnail = images[0]["url"] if images else None
    owner = playlist.get("owner", {}).get("display_name", "")

    return BrowseMediaItem(
        title=playlist_name,
        media_class=MediaClass.PLAYLIST,
        media_type=MediaContentType.PLAYLIST,
        media_id=f"playlist_{playlist_id}",
        can_browse=True,
        can_play=True,
        thumbnail=thumbnail,
        subtitle=f"by {owner}" if owner else None,
    )


def _get_page(options) -> int:
    if hasattr(options, "paging") and options.paging and hasattr(options.paging, "page") and options.paging.page:
        return options.paging.page
    return 1


def _get_limit(options, default: int = 50) -> int:
    if hasattr(options, "paging") and options.paging and hasattr(options.paging, "limit") and options.paging.limit:
        return options.paging.limit
    return default


def _empty_browse(media_id: str, title: str, page: int, limit: int) -> BrowseResults:
    return BrowseResults(
        media=BrowseMediaItem(
            title=title,
            media_class=MediaClass.DIRECTORY,
            media_type="directory",
            media_id=media_id,
            can_browse=True,
            items=[],
        ),
        pagination=Pagination(page=page, limit=limit, count=0),
    )
