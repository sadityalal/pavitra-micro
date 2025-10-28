import React, { useEffect, useState } from 'react';
import { useLocation } from 'react-router-dom';
import { productService } from '../services/productService';
import ProductCard from '../components/common/ProductCard';

function useQuery() {
  return new URLSearchParams(useLocation().search);
}

const SearchResults = () => {
  const q = useQuery().get('q') || '';
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const load = async () => {
      if (!q) return setResults([]);
      setLoading(true);
      try {
        const res = await productService.searchProducts(q);
        setResults(res.products || []);
      } catch (e) {
        console.error('Search failed', e);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [q]);

  return (
    <div className="container py-4">
      <h2>Search Results for "{q}"</h2>
      {loading && <p>Searching...</p>}
      <div className="row">
        {results.map(p => (
          <div className="col-md-3 mb-4" key={p.id}>
            <ProductCard product={p} />
          </div>
        ))}
      </div>
    </div>
  );
};

export default SearchResults;
