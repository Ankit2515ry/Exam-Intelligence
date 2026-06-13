// import { useEffect, useState } from 'react';
// import { Link, useNavigate } from 'react-router-dom';
// import { LayoutDashboard, MessageSquare, LogOut, UploadCloud, Trash2, FileText } from 'lucide-react';
// import { uploadService } from '../api/apiService';

// export default function Dashboard() {
//   const navigate = useNavigate();
//   const [documents, setDocuments] = useState([]);
//   const [uploading, setUploading] = useState(false);

//   const loadDocs = async () => {
//     try {
//       const data = await uploadService.getDocuments();
//       setDocuments(Array.isArray(data) ? data : []);
//     } catch (err) {
//       console.error("Error loading documents index", err);
//     }
//   };

//   useEffect(() => {
//     loadDocs();
//   }, []);

//   const handleFileUpload = async (e) => {
//     const file = e.target.files[0];
//     if (!file) return;
//     setUploading(true);
//     try {
//       await uploadService.uploadFile(file);
//       loadDocs(); 
//     } catch (err) {
//       alert(err.response?.data?.detail || "Upload error context occurred.");
//     } finally {
//       setUploading(false);
//     }
//   };

//   const handleDelete = async (uuid) => {
//     if (!confirm("Confirm document deletion?")) return;
//     try {
//       await uploadService.deleteDocument(uuid);
//       loadDocs();
//     } catch (err) {
//       alert("Failed to delete the index file.");
//     }
//   };

//   // SIGN OUT FUNCTION
//   const handleSignOut = () => {
//     localStorage.removeItem('userToken'); // Delete JWT token securely
//     navigate('/'); // Route back to Sign In shell
//   };

//   return (
//     <div className="flex h-screen bg-slate-100">
//       <aside className="w-64 bg-slate-900 text-white flex flex-col justify-between p-4">
//         <div className="space-y-6">
//           <div className="text-xl font-bold px-2 tracking-wide">Exam Intelligence</div>
//           <nav className="space-y-2">
//             <Link to="/dashboard" className="flex items-center gap-3 bg-indigo-600 px-4 py-2.5 rounded-lg font-medium"><LayoutDashboard size={20} /> Dashboard</Link>
//             <Link to="/chat" className="flex items-center gap-3 text-slate-400 hover:bg-slate-800 hover:text-white px-4 py-2.5 rounded-lg font-medium transition"><MessageSquare size={20} /> Chat Module</Link>
//           </nav>
//         </div>

//         {/* Added Sign Out Action Button */}
//         <button 
//           onClick={handleSignOut} 
//           className="flex items-center gap-3 text-rose-400 hover:bg-rose-950/40 px-4 py-2.5 rounded-lg font-medium transition cursor-pointer text-left w-full mt-auto"
//         >
//           <LogOut size={20} /> Sign Out
//         </button>
//       </aside>

//       <main className="flex-1 p-8 overflow-y-auto">
//         <header className="flex justify-between items-center mb-8">
//           <div>
//             <h1 className="text-3xl font-bold text-slate-800">Knowledge Repository</h1>
//             <p className="text-slate-500 text-sm">Upload context documents to ground your RAG processing engine.</p>
//           </div>
          
//           <label className="flex items-center gap-2 bg-indigo-600 text-white px-4 py-2 rounded-lg cursor-pointer font-medium hover:bg-indigo-700 transition">
//             <UploadCloud size={20} />
//             {uploading ? "Ingesting Engine..." : "Upload Context PDF"}
//             <input type="file" accept="application/pdf" onChange={handleFileUpload} className="hidden" disabled={uploading} />
//           </label>
//         </header>

//         <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
//           {documents.length === 0 ? (
//             <div className="p-12 text-center text-slate-400">No context data sources linked to this agent profile container yet.</div>
//           ) : (
//             <table className="w-full text-left border-collapse">
//               <thead>
//                 <tr className="bg-slate-50 border-b border-slate-200 text-xs font-bold text-slate-400 uppercase tracking-wider">
//                   <th className="p-4">Resource Document Title</th>
//                   <th className="p-4">System Key / UUID</th>
//                   <th className="p-4 text-right">Actions</th>
//                 </tr>
//               </thead>
//               <tbody className="divide-y divide-slate-100 text-sm text-slate-700">
//                 {documents.map((doc) => (
//                   <tr key={doc.id} className="hover:bg-slate-50/80">
//                     <td className="p-4 flex items-center gap-2 font-medium text-slate-800"><FileText size={18} className="text-indigo-500" /> {doc.filename}</td>
//                     <td className="p-4 font-mono text-xs text-slate-400">{doc.document_uuid}</td>
//                     <td className="p-4 text-right">
//                       <button onClick={() => handleDelete(doc.document_uuid)} className="text-red-500 hover:bg-red-50 p-2 rounded-lg transition"><Trash2 size={16} /></button>
//                     </td>
//                   </tr>
//                 ))}
//               </tbody>
//             </table>
//           )}
//         </div>
//       </main>
//     </div>
//   );
// }

import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import {
  LayoutDashboard,
  MessageSquare,
  LogOut,
  UploadCloud,
  Trash2,
  FileText,
  Eye,
} from "lucide-react";

import { uploadService } from "../api/apiService";

export default function Dashboard() {
  const navigate = useNavigate();

  const [documents, setDocuments] = useState([]);
  const [uploading, setUploading] = useState(false);

  const loadDocs = async () => {
    try {
      const data = await uploadService.getDocuments();

      setDocuments(
        Array.isArray(data) ? data : []
      );
    } catch (err) {
      console.error(
        "Error loading documents",
        err
      );
    }
  };

  useEffect(() => {
    loadDocs();
  }, []);

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];

    if (!file) return;

    setUploading(true);

    try {
      await uploadService.uploadFile(file);

      await loadDocs();
    } catch (err) {
      alert(
        err.response?.data?.detail ||
          "Upload failed."
      );
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (
    documentUuid
  ) => {
    const confirmDelete = window.confirm(
      "Are you sure you want to delete this document?"
    );

    if (!confirmDelete) return;

    try {
      await uploadService.deleteDocument(
        documentUuid
      );

      await loadDocs();
    } catch (err) {
      console.error(err);

      alert(
        "Failed to delete document."
      );
    }
  };

  // const handleViewPdf = (
  //   documentUuid
  // ) => {
  //   window.open(
  //     `http://localhost:8000/api/view/${documentUuid}`,
  //     "_blank"
  //   );
  // };

  const handleViewPdf = async (documentUuid) => {

    try {

      await uploadService.viewPdf(
        documentUuid
      );

    } catch (err) {

      console.error(err);

      alert(
        err.response?.data?.detail ||
        err.message ||
        "Unknown Error"
      );
    }
  };


  const handleSignOut = () => {
    localStorage.removeItem(
      "userToken"
    );

    navigate("/");
  };

  return (
    <div className="flex h-screen bg-slate-100">

      {/* Sidebar */}
      <aside className="w-64 bg-slate-900 text-white flex flex-col justify-between p-4">

        <div className="space-y-6">

          <div className="text-xl font-bold px-2 tracking-wide">
            Exam Intelligence
          </div>

          <nav className="space-y-2">

            <Link
              to="/dashboard"
              className="flex items-center gap-3 bg-indigo-600 px-4 py-2.5 rounded-lg font-medium"
            >
              <LayoutDashboard size={20} />
              Dashboard
            </Link>

            <Link
              to="/chat"
              className="flex items-center gap-3 text-slate-400 hover:bg-slate-800 hover:text-white px-4 py-2.5 rounded-lg font-medium transition"
            >
              <MessageSquare size={20} />
              Chat Module
            </Link>

          </nav>
        </div>

        <button
          onClick={handleSignOut}
          className="flex items-center gap-3 text-rose-400 hover:bg-rose-950/40 px-4 py-2.5 rounded-lg font-medium transition cursor-pointer text-left w-full"
        >
          <LogOut size={20} />
          Sign Out
        </button>

      </aside>

      {/* Main Content */}
      <main className="flex-1 p-8 overflow-y-auto">

        <header className="flex justify-between items-center mb-8">

          <div>
            <h1 className="text-3xl font-bold text-slate-800">
              Knowledge Repository
            </h1>

            <p className="text-slate-500 text-sm">
              Upload documents to ground
              your AI responses.
            </p>
          </div>

          <label className="flex items-center gap-2 bg-indigo-600 text-white px-4 py-2 rounded-lg cursor-pointer font-medium hover:bg-indigo-700 transition">

            <UploadCloud size={20} />

            {uploading
              ? "Uploading..."
              : "Upload PDF"}

            <input
              type="file"
              accept="application/pdf"
              onChange={
                handleFileUpload
              }
              className="hidden"
              disabled={uploading}
            />

          </label>

        </header>

        <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">

          {documents.length === 0 ? (

            <div className="p-12 text-center text-slate-400">
              No uploaded documents.
            </div>

          ) : (

            <table className="w-full text-left border-collapse">

              <thead>

                <tr className="bg-slate-50 border-b border-slate-200 text-xs font-bold text-slate-400 uppercase tracking-wider">

                  <th className="p-4">
                    Document
                  </th>

                  <th className="p-4">
                    UUID
                  </th>

                  <th className="p-4 text-right">
                    Actions
                  </th>

                </tr>

              </thead>

              <tbody className="divide-y divide-slate-100 text-sm text-slate-700">

                {documents.map((doc) => (

                  <tr
                    key={doc.id}
                    className="hover:bg-slate-50"
                  >

                    <td className="p-4 flex items-center gap-2 font-medium text-slate-800">

                      <FileText
                        size={18}
                        className="text-indigo-500"
                      />

                      {doc.filename}

                    </td>

                    <td className="p-4 font-mono text-xs text-slate-400">
                      {doc.document_uuid}
                    </td>

                    <td className="p-4 text-right">

                      <button
                        onClick={() =>
                          handleViewPdf(
                            doc.document_uuid
                          )
                        }
                        className="text-blue-500 hover:bg-blue-50 p-2 rounded-lg transition mr-2"
                        title="View PDF"
                      >
                        <Eye size={16} />
                      </button>

                      <button
                        onClick={() =>
                          handleDelete(
                            doc.document_uuid
                          )
                        }
                        className="text-red-500 hover:bg-red-50 p-2 rounded-lg transition"
                        title="Delete PDF"
                      >
                        <Trash2 size={16} />
                      </button>

                    </td>

                  </tr>

                ))}

              </tbody>

            </table>

          )}

        </div>

      </main>

    </div>
  );
}