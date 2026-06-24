import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 15000
})

// Video list
export function getVideos(page = 1, limit = 25) {
  return api.get('/videos', { params: { page, limit } })
}

// Single video detail
export function getVideoDetail(id) {
  return api.get(`/video/${encodeURIComponent(id)}`)
}

// Record play
export function recordPlay(id) {
  return api.post(`/video/${encodeURIComponent(id)}/play`)
}

// Get comments
export function getComments(videoId, page = 1, limit = 20) {
  return api.get(`/video/${encodeURIComponent(videoId)}/comments`, { params: { page, limit } })
}

// Post comment
export function postComment(videoId, content, username = '匿名用户') {
  return api.post(`/video/${encodeURIComponent(videoId)}/comments`, { content, username })
}

// Delete comment
export function deleteComment(commentId) {
  return api.delete(`/comment/${commentId}`)
}

// Get danmaku
export function getDanmaku(videoId) {
  return api.get(`/video/${encodeURIComponent(videoId)}/danmaku`)
}

// Send danmaku
export function sendDanmaku(videoId, data) {
  return api.post(`/video/${encodeURIComponent(videoId)}/danmaku`, data)
}

// Like video
export function likeVideo(videoId, username = '匿名用户') {
  return api.post(`/video/${encodeURIComponent(videoId)}/like`, { username })
}

// Follow UP主
export function followUp(videoId, username = '匿名用户') {
  return api.post(`/video/${encodeURIComponent(videoId)}/follow`, { username })
}

export function getVideoStream(id) {
  return `/video/${encodeURIComponent(id)}/stream`
}

export function getThumbnail(id) {
  return `/thumbnails/${encodeURIComponent(id)}.jpg`
}
