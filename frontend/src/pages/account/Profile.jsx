import React, { useEffect, useState } from 'react';
import { userService } from '../../services/userService';

const Profile = () => {
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      try {
        const res = await userService.getProfile();
        setProfile(res || null);
      } catch (e) {
        console.error('Failed to load profile', e);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  const handleSave = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      await userService.updateProfile(profile);
      alert('Profile updated');
    } catch (err) {
      console.error(err);
      alert('Failed to update profile');
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <div className="container py-5 text-center">Loading profile...</div>;
  if (!profile) return <div className="container py-5 text-center">No profile found</div>;

  return (
    <div className="container py-4">
      <h2>Profile</h2>
      <form onSubmit={handleSave} className="mt-3">
        <div className="mb-3">
          <label className="form-label">Name</label>
          <input className="form-control" value={profile.name || ''} onChange={e => setProfile({ ...profile, name: e.target.value })} />
        </div>
        <div className="mb-3">
          <label className="form-label">Email</label>
          <input className="form-control" value={profile.email || ''} disabled />
        </div>
        <button className="btn btn-primary" disabled={saving}>{saving ? 'Saving...' : 'Save'}</button>
      </form>
    </div>
  );
};

export default Profile;
