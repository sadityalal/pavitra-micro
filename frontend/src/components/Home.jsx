import React from 'react'
import { Link } from 'react-router-dom'

const Home = () => {
  return (
    <div>
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <h1 className="text-3xl font-bold text-gray-900">Pavitra Trading</h1>
          <p className="text-gray-600">Your trusted shopping destination</p>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-8">
        <div className="text-center">
          <h2 className="text-4xl font-bold text-gray-900 mb-4">
            Welcome to Pavitra Trading
          </h2>
          <p className="text-xl text-gray-600 mb-8">
            Discover amazing products at great prices
          </p>
          
          <div className="space-x-4">
            <Link
              to="/products"
              className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700"
            >
              Shop Now
            </Link>
            <Link
              to="/register"
              className="border border-blue-600 text-blue-600 px-6 py-3 rounded-lg hover:bg-blue-50"
            >
              Create Account
            </Link>
          </div>
        </div>
      </main>
    </div>
  )
}

export default Home
