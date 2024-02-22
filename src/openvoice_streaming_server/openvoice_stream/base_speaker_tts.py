import re
import torch

from openvoice.api import BaseSpeakerTTS


class StreamingBaseSpeakerTTS(BaseSpeakerTTS):
    language_marks = {
        "english": "EN",
        "chinese": "ZH",
    }

    async def generate_audio_chunks(self, text, speaker, language='English', speed=1.0):
        mark = self.language_marks.get(language.lower(), None)
        assert mark is not None, f"language {language} is not supported"

        texts = self.split_sentences_into_pieces(text, mark)

        for t in texts:
            t = re.sub(r'([a-z])([A-Z])', r'\1 \2', t)
            t = f'[{mark}]{t}[{mark}]'
            stn_tst = self.get_text(t, self.hps, False)
            device = self.device
            speaker_id = self.hps.speakers[speaker]
            with torch.no_grad():
                x_tst = stn_tst.unsqueeze(0).to(device)
                x_tst_lengths = torch.LongTensor([stn_tst.size(0)]).to(device)
                sid = torch.LongTensor([speaker_id]).to(device)
                audio = self.model.infer(x_tst, x_tst_lengths, sid=sid, noise_scale=0.667, noise_scale_w=0.6,
                                         length_scale=1.0 / speed)[0][0, 0].data.cpu().float().numpy()
                yield audio

    async def tts_stream(self, text, speaker, language='English', speed=1.0):
        async for audio_chunk in self.generate_audio_chunks(text, speaker, language, speed):
            yield audio_chunk.tobytes()
