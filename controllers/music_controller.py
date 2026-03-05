import pygame
import os


class MusicController:

    def __init__(self):

        pygame.mixer.init()

        self.music_playing = False

        self.songs = [
            "assets/song-1.mp3",
            "assets/song-2.mp3",
            "assets/song-3.mp3"
        ]

        self.current_index = 0

        self.load_song()


    def load_song(self):

        song = self.songs[self.current_index]

        if not os.path.exists(song):
            print("ERROR: File not found:", song)
            return

        pygame.mixer.music.load(song)

        print("Loaded:", song)


    def toggle_play_pause(self):

        if not self.music_playing:

            pygame.mixer.music.play()
            self.music_playing = True
            print("Music Playing")

        else:

            pygame.mixer.music.pause()
            self.music_playing = False
            print("Music Paused")


    def stop_music(self):

        pygame.mixer.music.stop()
        self.music_playing = False
        print("Music Stopped")


    def next_track(self):

        self.current_index = (self.current_index + 1) % len(self.songs)

        self.load_song()

        pygame.mixer.music.play()
        self.music_playing = True

        print("Next Track")


    def prev_track(self):

        self.current_index = (self.current_index - 1) % len(self.songs)

        self.load_song()

        pygame.mixer.music.play()
        self.music_playing = True

        print("Previous Track")


    def get_status(self):

        if self.music_playing:
            return "Playing"
        else:
            return "Paused"