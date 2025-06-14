# api/get-subtitles.py

from http.server import BaseHTTPRequestHandler
import json
from urllib.parse import urlparse, parse_qs
from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound, TranscriptsDisabled, VideoUnavailable

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        # リクエストボディからデータを読み込む
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        try:
            body = json.loads(post_data)
            video_id = body.get('video_id')
            language_codes = [body.get('language', 'en')] # デフォルトは英語

            if not video_id:
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'video_id is required'}).encode('utf-8'))
                return

            # youtube-transcript-api を使用して字幕を取得
            try:
                # 指定された言語での取得を試みる
                transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=language_codes)
                
                # 動画タイトルを取得（これはオプションですが、UIで役立ちます）
                # 注意: この方法は公式APIではないため、将来変更される可能性があります。
                # より安定した方法を使いたい場合は、YouTube Data API v3の利用を検討してください。
                video_title = f"Video ID: {video_id}" # シンプルなフォールバック
                try:
                    from youtube_transcript_api.transcripts import TranscriptListFetcher
                    fetcher = TranscriptListFetcher(None, None)
                    video_title = fetcher.fetch(video_id).video_title
                except Exception:
                    pass # タイトル取得に失敗しても処理は続行

                response_data = {
                    "title": video_title,
                    "subtitles": transcript_list
                }
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(response_data).encode('utf-8'))

            except (NoTranscriptFound, TranscriptsDisabled, VideoUnavailable) as e:
                # APIが返す特定の例外をハンドリング
                error_message = 'An unknown error occurred'
                if isinstance(e, NoTranscriptFound):
                    error_message = f"No transcript found for language codes: {language_codes}"
                elif isinstance(e, TranscriptsDisabled):
                    error_message = 'Transcripts are disabled for this video.'
                elif isinstance(e, VideoUnavailable):
                    error_message = 'The video is unavailable.'
                
                self.send_response(404)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': error_message, 'type': type(e).__name__}).encode('utf-8'))

        except Exception as e:
            # その他の予期せぬエラー
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))

        return
