import React, { useState } from 'react';
import { useSettingsContext } from '../../contexts/SettingsContext';
import { useAuth } from '../../contexts/AuthContext';

const AdminSettings = () => {
  const { 
    siteSettings, 
    siteSettingsLoading, 
    siteSettingsError, 
    updateSiteSettings,
    canManageSettings 
  } = useSettingsContext();
  
  const { isAuthenticated, isAdmin } = useAuth();
  const [isEditing, setIsEditing] = useState(false);
  const [formData, setFormData] = useState({});
  const [saveLoading, setSaveLoading] = useState(false);

  // Initialize form data when settings load
  React.useEffect(() => {
    if (siteSettings) {
      setFormData(siteSettings);
    }
  }, [siteSettings]);

  const handleInputChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleSave = async () => {
    try {
      setSaveLoading(true);
      await updateSiteSettings(formData);
      setIsEditing(false);
    } catch (error) {
      console.error('Failed to save settings:', error);
    } finally {
      setSaveLoading(false);
    }
  };

  const handleCancel = () => {
    setFormData(siteSettings);
    setIsEditing(false);
  };

  if (!isAuthenticated || !isAdmin()) {
    return (
      <div className="alert alert-warning">
        <i className="bi bi-shield-exclamation me-2"></i>
        Admin access required to view site settings.
      </div>
    );
  }

  if (siteSettingsLoading) {
    return (
      <div className="text-center py-4">
        <div className="spinner-border" role="status">
          <span className="visually-hidden">Loading settings...</span>
        </div>
      </div>
    );
  }

  if (siteSettingsError) {
    return (
      <div className="alert alert-danger">
        <i className="bi bi-exclamation-triangle me-2"></i>
        Error loading settings: {siteSettingsError}
      </div>
    );
  }

  return (
    <div className="admin-settings">
      <div className="d-flex justify-content-between align-items-center mb-4">
        <h4>Site Settings</h4>
        {!isEditing ? (
          <button 
            className="btn btn-primary"
            onClick={() => setIsEditing(true)}
          >
            <i className="bi bi-pencil me-2"></i>
            Edit Settings
          </button>
        ) : (
          <div>
            <button 
              className="btn btn-success me-2"
              onClick={handleSave}
              disabled={saveLoading}
            >
              {saveLoading ? (
                <>
                  <span className="spinner-border spinner-border-sm me-2" />
                  Saving...
                </>
              ) : (
                <>
                  <i className="bi bi-check me-2"></i>
                  Save
                </>
              )}
            </button>
            <button 
              className="btn btn-secondary"
              onClick={handleCancel}
            >
              <i className="bi bi-x me-2"></i>
              Cancel
            </button>
          </div>
        )}
      </div>

      <div className="card">
        <div className="card-body">
          {isEditing ? (
            <div className="row g-3">
              <div className="col-md-6">
                <label className="form-label">Site Name</label>
                <input
                  type="text"
                  className="form-control"
                  value={formData.site_name || ''}
                  onChange={(e) => handleInputChange('site_name', e.target.value)}
                />
              </div>
              <div className="col-md-6">
                <label className="form-label">Currency</label>
                <input
                  type="text"
                  className="form-control"
                  value={formData.currency || ''}
                  onChange={(e) => handleInputChange('currency', e.target.value)}
                />
              </div>
              <div className="col-md-6">
                <label className="form-label">Maintenance Mode</label>
                <select
                  className="form-select"
                  value={formData.maintenance_mode || false}
                  onChange={(e) => handleInputChange('maintenance_mode', e.target.value === 'true')}
                >
                  <option value={false}>Disabled</option>
                  <option value={true}>Enabled</option>
                </select>
              </div>
            </div>
          ) : (
            <div className="row">
              <div className="col-md-6">
                <table className="table table-striped">
                  <tbody>
                    <tr>
                      <th>Site Name</th>
                      <td>{siteSettings?.site_name}</td>
                    </tr>
                    <tr>
                      <th>Currency</th>
                      <td>{siteSettings?.currency}</td>
                    </tr>
                    <tr>
                      <th>Maintenance Mode</th>
                      <td>
                        <span className={`badge ${siteSettings?.maintenance_mode ? 'bg-warning' : 'bg-success'}`}>
                          {siteSettings?.maintenance_mode ? 'Enabled' : 'Disabled'}
                        </span>
                      </td>
                    </tr>
                    <tr>
                      <th>Debug Mode</th>
                      <td>
                        <span className={`badge ${siteSettings?.debug_mode ? 'bg-info' : 'bg-secondary'}`}>
                          {siteSettings?.debug_mode ? 'Enabled' : 'Disabled'}
                        </span>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default AdminSettings;
