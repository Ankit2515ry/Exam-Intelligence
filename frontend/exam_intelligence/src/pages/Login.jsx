import { useForm } from 'react-hook-form';
import { useNavigate, Link } from 'react-router-dom';
import { authService } from '../api/apiService';
import { useState } from 'react';

export default function Login() {
  const { register, handleSubmit } = useForm();
  const navigate = useNavigate();
  const [error, setError] = useState("");

  const onSubmit = async (data) => {
    try {
      setError("");
      const response = await authService.login(data);
      
      // Save your true JWT access token
      localStorage.setItem("userToken", response.access_token);
      
      navigate('/dashboard');
    } catch (err) {
      setError(err.response?.data?.detail || "Invalid Email or Password entry.");
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 px-4">
      <div className="max-w-md w-full bg-white p-8 rounded-xl shadow-md border border-slate-100">
        <h2 className="text-2xl font-bold text-center mb-6 text-slate-800">Exam Intelligence</h2>
        
        {error && (
          <div className="mb-4 text-sm text-red-600 bg-red-50 p-2.5 rounded border border-red-100">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-500 mb-1">Email Address</label>
            <input {...register("email")} type="email" placeholder="you@example.com" required className="w-full px-4 py-2 border rounded-lg focus:outline-indigo-500 text-sm" />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-500 mb-1">Password</label>
            <input {...register("password")} type="password" placeholder="••••••••" required className="w-full px-4 py-2 border rounded-lg focus:outline-indigo-500 text-sm" />
          </div>
          <button type="submit" className="w-full bg-indigo-600 text-white py-2 rounded-lg font-semibold hover:bg-indigo-700 transition cursor-pointer text-sm">
            Sign In
          </button>
        </form>

        <p className="mt-6 text-sm text-center text-slate-500">
          Don't have an account?{" "}
          <Link to="/signup" className="text-indigo-600 hover:underline font-medium">
            Sign up
          </Link>
        </p>
      </div>
    </div>
  );
}