import { useState } from "react";

export const AVATAR_COLORS = [
  "#5b3df0",
  "#0f766e",
  "#b45309",
  "#be185d",
  "#1d4ed8",
  "#15803d",
  "#9333ea",
  "#b91c1c",
];

export const DEFAULT_AVATAR_COLOR = AVATAR_COLORS[0];

function initialsFor(user) {
  const source = (user?.display_name || user?.username || "?").trim();
  const parts = source.split(/\s+/).filter(Boolean);
  if (parts.length >= 2) {
    return (parts[0][0] + parts[1][0]).toUpperCase();
  }
  return source.slice(0, 2).toUpperCase();
}

function Avatar({ user, size = 32 }) {
  const [imageFailed, setImageFailed] = useState(false);
  const showImage = user?.avatar_url && !imageFailed;

  const style = {
    width: size,
    height: size,
    fontSize: Math.max(10, size * 0.4),
  };

  if (showImage) {
    return (
      <img
        className="avatar"
        style={style}
        src={user.avatar_url}
        alt={user.display_name || user.username}
        onError={() => setImageFailed(true)}
      />
    );
  }

  return (
    <span
      className="avatar avatar-initials"
      style={{ ...style, backgroundColor: user?.avatar_color || DEFAULT_AVATAR_COLOR }}
    >
      {initialsFor(user)}
    </span>
  );
}

export default Avatar;
