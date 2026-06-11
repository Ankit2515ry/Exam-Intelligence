import { useForm } from 'react-hook-form';
import { useNavigate, Link } from 'react-router-dom';
import { authService } from '../api/apiService';
import { useState } from 'react';

export default function Signup() {
  // Clearer form register management
  const { register, handleSubmit } = useForm();
  const navigate = useNavigate();
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);

  const onSubmit = async (data) => {
    try {
      setError("");
      await authService.signup(data);
      setSuccess(true);
      
      setTimeout(() => {
        navigate('/'); // Redirect to login page upon completion
      }, 1500);
    } catch (err) {
      const backendDetail = err.response?.data?.detail;
      
      // If FastAPI throws a Pydantic validation error array, extract the message cleanly
      if (Array.isArray(backendDetail)) {
        setError(backendDetail[0]?.msg || "Invalid data format submitted.");
      } else {
        setError(backendDetail || "Registration processing failed.");
      }
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 px-4">
      <div className="max-w-md w-full bg-white p-8 rounded-xl shadow-md border border-slate-100">
        <h2 className="text-2xl font-bold text-center mb-6 text-slate-800">Create Account</h2>
        
        {error && (
          <div className="mb-4 text-sm text-red-600 bg-red-50 p-2.5 rounded border border-red-100">
            {error}
          </div>
        )}

        {success && (
          <div className="mb-4 text-sm text-emerald-600 bg-emerald-50 p-2.5 rounded border border-emerald-100">
            Account created! Redirecting to login screen...
          </div>
        )}

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-500 mb-1">Full Name</label>
            <input 
              {...register("name", { required: "Name is required" })} 
              type="text" 
              placeholder="Ankit" 
              className="w-full px-4 py-2 border border-slate-200 rounded-lg focus:outline-none focus:border-indigo-500 text-sm" 
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-500 mb-1">Email Address</label>
            <input 
              {...register("email", { required: "Email is required" })} 
              type="email" 
              placeholder="ankit@example.com" 
              className="w-full px-4 py-2 border border-slate-200 rounded-lg focus:outline-none focus:border-indigo-500 text-sm" 
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-500 mb-1">Password</label>
            <input 
              {...register("password", { required: "Password is required" })} 
              type="password" 
              placeholder="••••••••" 
              className="w-full px-4 py-2 border border-slate-200 rounded-lg focus:outline-none focus:border-indigo-500 text-sm" 
            />
          </div>
          <button 
            type="submit" 
            className="w-full bg-indigo-600 text-white py-2 rounded-lg font-semibold hover:bg-indigo-700 transition cursor-pointer text-sm"
          >
            Register
          </button>
        </form>

        <p className="mt-6 text-sm text-center text-slate-500">
          Already have an account?{" "}
          <Link to="/" className="text-indigo-600 hover:underline font-medium">
            Sign In
          </Link>
        </p>
      </div>
    </div>
  );
}