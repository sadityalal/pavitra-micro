import React, { useEffect, useState } from 'react';
import { userService } from '../../services/userService';

const Addresses = () => {
  const [addresses, setAddresses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [newAddr, setNewAddr] = useState({ line1: '', city: '', postal_code: '' });

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      try {
        const res = await userService.getAddresses();
        setAddresses(res || []);
      } catch (e) {
        console.error('Failed to load addresses', e);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  const handleAdd = async (e) => {
    e.preventDefault();
    try {
      const res = await userService.addAddress(newAddr);
      setAddresses(prev => [...prev, res]);
      setNewAddr({ line1: '', city: '', postal_code: '' });
    } catch (err) {
      console.error(err);
      alert('Failed to add address');
    }
  };

  const handleDelete = async (id) => {
    if (!confirm('Delete address?')) return;
    try {
      await userService.deleteAddress(id);
      setAddresses(prev => prev.filter(a => a.id !== id));
    } catch (err) {
      console.error(err);
      alert('Failed to delete address');
    }
  };

  if (loading) return <div className="container py-5 text-center">Loading addresses...</div>;

  return (
    <div className="container py-4">
      <h2>Addresses</h2>
      <div className="mb-4">
        {addresses.map(a => (
          <div key={a.id} className="card mb-2">
            <div className="card-body d-flex justify-content-between">
              <div>
                <div><strong>{a.line1}</strong></div>
                <div className="small">{a.city} {a.postal_code}</div>
              </div>
              <div>
                <button className="btn btn-sm btn-danger" onClick={() => handleDelete(a.id)}>Delete</button>
              </div>
            </div>
          </div>
        ))}
      </div>

      <h4>Add address</h4>
      <form onSubmit={handleAdd} className="row g-2">
        <div className="col-12">
          <input className="form-control" placeholder="Address line 1" value={newAddr.line1} onChange={e => setNewAddr({ ...newAddr, line1: e.target.value })} />
        </div>
        <div className="col-md-6">
          <input className="form-control" placeholder="City" value={newAddr.city} onChange={e => setNewAddr({ ...newAddr, city: e.target.value })} />
        </div>
        <div className="col-md-4">
          <input className="form-control" placeholder="Postal code" value={newAddr.postal_code} onChange={e => setNewAddr({ ...newAddr, postal_code: e.target.value })} />
        </div>
        <div className="col-md-2">
          <button className="btn btn-primary w-100">Add</button>
        </div>
      </form>
    </div>
  );
};

export default Addresses;
