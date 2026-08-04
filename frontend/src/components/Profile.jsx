/*
 * SPDX-License-Identifier: AGPL-3.0-or-later
 * Copyright (C) 2026 SpyrosDr
 */

import { useState } from "react";
import { updateProfile } from "../api";
import Avatar, { AVATAR_COLORS, DEFAULT_AVATAR_COLOR } from "./Avatar";
import ChangePassword from "./ChangePassword";

function Profile({ user, onUpdated }) {
  const [username, setUsername] = useState(user.username);
  const [displayName, setDisplayName] = useState(user.display_name || "");
  const [avatarUrl, setAvatarUrl] = useState(user.avatar_url || "");
  const [avatarColor, setAvatarColor] = useState(
    user.avatar_color || DEFAULT_AVATAR_COLOR
  );
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);

  const previewUser = {
    id: user.id,
    username,
    display_name: displayName,
    avatar_url: avatarUrl,
    avatar_color: avatarColor,
  };

  async function handleSave() {
    setLoading(true);
    setError(null);
    setSuccess(false);
    try {
      const updated = await updateProfile({
        username,
        display_name: displayName,
        avatar_url: avatarUrl,
        avatar_color: avatarColor,
      });
      onUpdated(updated);
      setSuccess(true);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <section className="card">
        <h2>Profile</h2>

        <div className="profile-avatar-row">
          <Avatar user={previewUser} size={56} />
          <p className="empty-state">
            Set an avatar by pasting a link to an image below, or leave blank
            for your initials in the color you pick.
          </p>
        </div>

        <label>
          Username
          <input value={username} onChange={(e) => setUsername(e.target.value)} />
        </label>
        <label>
          Display name (optional)
          <input
            value={displayName}
            onChange={(e) => setDisplayName(e.target.value)}
            placeholder="Shown instead of your username, e.g. Alan Carter"
          />
        </label>
        <label>
          Avatar image URL (optional)
          <input
            value={avatarUrl}
            onChange={(e) => setAvatarUrl(e.target.value)}
            placeholder="https://..."
          />
        </label>
        <label>
          Avatar color
          <div className="color-swatch-row">
            {AVATAR_COLORS.map((color) => (
              <button
                type="button"
                key={color}
                className={
                  "color-swatch" + (avatarColor === color ? " selected" : "")
                }
                style={{ backgroundColor: color }}
                onClick={() => setAvatarColor(color)}
                aria-label={`Use ${color} as avatar color`}
              />
            ))}
          </div>
        </label>

        <button onClick={handleSave} disabled={loading || !username}>
          {loading ? "Saving..." : "Save Profile"}
        </button>

        {error && <p className="error-text">{error}</p>}
        {success && <p className="empty-state">Profile updated.</p>}
      </section>

      <ChangePassword />
    </>
  );
}

export default Profile;
