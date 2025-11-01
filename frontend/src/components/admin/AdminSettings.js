// frontend/src/components/admin/AdminSettings.js
import React, { useState, useEffect } from 'react';
import { useSettings } from '../../contexts/SettingsContext';
import { useAuth } from '../../contexts/AuthContext';

const AdminSettings = () => {
  const {
    siteSettings,
    frontendSettings,
    refreshSiteSettings,
    canAccessAdminSettings
  } = useSettings();
  
  const { isAuthenticated, isAdmin } = useAuth();
  const [isEditing, setIsEditing] = useState(false);
  const [formData, setFormData] = useState({});
  const [saveLoading, setSaveLoading] = useState(false);

  useEffect(() => {
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
      // Here you would call the API to update site settings
      // await authService.updateSiteSettings(formData);
      console.log('Saving site settings:', formData);
      await refreshSiteSettings();
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

  if (!canAccessAdminSettings) {
    return (
      <div className="alert alert-warning">
        <i className="bi bi-shield-exclamation me-2"></i>
        You don't have permission to access admin settings.
      </div>
    );
  }

  return (
    <div className="admin-settings">
      <div className="d-flex justify-content-between align-items-center mb-4">
        <h4>Admin Site Settings</h4>
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

      <div className="row">
        <div className="col-md-6">
          <div className="card">
            <div className="card-header">
              <h5 className="card-title mb-0">Site Settings (Admin Only)</h5>
            </div>
            <div className="card-body">
              {isEditing ? (
                <div className="row g-3">
                  <div className="col-12">
                    <label className="form-label">Site Name</label>
                    <input
                      type="text"
                      className="form-control"
                      value={formData.site_name || ''}
                      onChange={(e) => handleInputChange('site_name', e.target.value)}
                    />
                  </div>
                  <div className="col-12">
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
                <table className="table table-striped">
                  <tbody>
                    <tr>
                      <th>Site Name</th>
                      <td>{siteSettings?.site_name || 'Not set'}</td>
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
              )}
            </div>
          </div>
        </div>

        <div className="col-md-6">
          <div className="card">
            <div className="card-header">
              <h5 className="card-title mb-0">Frontend Settings (Public)</h5>
            </div>
            <div className="card-body">
              <table className="table table-striped">
                <tbody>
                  <tr>
                    <th>Currency</th>
                    <td>{frontendSettings?.currency}</td>
                  </tr>
                  <tr>
                    <th>Free Shipping Min Amount</th>
                    <td>{frontendSettings?.currency_symbol}{frontendSettings?.free_shipping_min_amount}</td>
                  </tr>
                  <tr>
                    <th>Return Period</th>
                    <td>{frontendSettings?.return_period_days} days</td>
                  </tr>
                  <tr>
                    <th>Guest Checkout</th>
                    <td>
                      <span className={`badge ${frontendSettings?.enable_guest_checkout ? 'bg-success' : 'bg-secondary'}`}>
                        {frontendSettings?.enable_guest_checkout ? 'Enabled' : 'Disabled'}
                      </span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdminSettings;