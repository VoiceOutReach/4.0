import { useRouter } from 'next/router';
import { useEffect, useState } from 'react';

export default function VoicePage() {
  const router = useRouter();
  const { id } = router.query;
  const [message, setMessage] = useState('');
  const [audioUrl, setAudioUrl] = useState('');

  useEffect(() => {
    if (id) {
      setAudioUrl(`/voices/${id}.mp3`);
      const defaultMsg = `Here’s your personalized message.`;
      setMessage(defaultMsg);
    }
  }, [id]);

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gray-900 text-white p-6">
      <h1 className="text-3xl font-bold mb-4">🎙️ Your Voice Note</h1>
      {audioUrl && (
        <audio controls autoPlay className="mb-4">
          <source src={audioUrl} type="audio/mpeg" />
          Your browser does not support the audio element.
        </audio>
      )}
      <p className="text-lg mb-6 text-center max-w-xl">{message}</p>
      <a
        href="https://www.linkedin.com/"
        target="_blank"
        className="bg-blue-500 hover:bg-blue-600 text-white font-bold py-2 px-4 rounded"
        rel="noopener noreferrer"
      >
        Reply on LinkedIn
      </a>
    </div>
  );
}
