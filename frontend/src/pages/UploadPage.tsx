interface Props {
  onDone: () => void;
}
export default function UploadPage({ onDone }: Props) {
  return <div>Upload page coming soon <button onClick={onDone}>Go to library</button></div>;
}
