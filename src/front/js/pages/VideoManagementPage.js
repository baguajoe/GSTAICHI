// import React, { useState, useEffect } from "react";

// const VideoManagementPage = () => {
//     const [videos, setVideos] = useState([]);
//     const [formData, setFormData] = useState({
//         title: "",
//         description: "",
//         price: 0.0,
//         category: "",
//     });
//     const [file, setFile] = useState(null);

//     useEffect(() => {
//         const fetchVideos = async () => {
//             const response = await fetch("/videos"); // Backend endpoint to get all videos
//             const data = await response.json();
//             setVideos(data.videos || []);
//         };
//         fetchVideos();
//     }, []);

//     const handleFileChange = (e) => {
//         setFile(e.target.files[0]);
//     };

//     const handleChange = (e) => {
//         setFormData({ ...formData, [e.target.name]: e.target.value });
//     };

//     const handleCreateVideo = async (e) => {
//         e.preventDefault();

//         // Create a FormData object for file upload
//         const uploadData = new FormData();
//         uploadData.append("file", file); // Append the video file
//         uploadData.append("title", formData.title);
//         uploadData.append("description", formData.description);
//         uploadData.append("price", formData.price);
//         uploadData.append("category", formData.category);

//         const response = await fetch("/video", {
//             method: "POST",
//             body: uploadData,
//         });
//         const data = await response.json();
//         alert(data.message || "Video created successfully!");
//         setFormData({ title: "", description: "", price: 0.0, category: "" });
//         setFile(null); // Reset file input
//         setVideos((prev) => [...prev, data.video]);
//     };

//     const handleDeleteVideo = async (videoId) => {
//         const response = await fetch(`/video/${videoId}`, {
//             method: "DELETE",
//         });
//         const data = await response.json();
//         alert(data.message || "Error deleting video");
//         setVideos((prev) => prev.filter((video) => video.id !== videoId));
//     };

//     return (
//         <div style={{ padding: "20px", maxWidth: "800px", margin: "0 auto" }}>
//             <h1>Video Management</h1>

//             {/* Video Creation Form */}
//             <form onSubmit={handleCreateVideo} style={{ marginBottom: "20px" }}>
//                 <input
//                     type="text"
//                     name="title"
//                     placeholder="Title"
//                     value={formData.title}
//                     onChange={handleChange}
//                     required
//                     style={{ display: "block", marginBottom: "10px" }}
//                 />
//                 <textarea
//                     name="description"
//                     placeholder="Description"
//                     value={formData.description}
//                     onChange={handleChange}
//                     style={{ display: "block", marginBottom: "10px" }}
//                 ></textarea>
//                 <input
//                     type="number"
//                     name="price"
//                     placeholder="Price"
//                     value={formData.price}
//                     onChange={handleChange}
//                     style={{ display: "block", marginBottom: "10px" }}
//                 />
//                 <input
//                     type="text"
//                     name="category"
//                     placeholder="Category"
//                     value={formData.category}
//                     onChange={handleChange}
//                     style={{ display: "block", marginBottom: "10px" }}
//                 />
//                 <input
//                     type="file"
//                     name="file"
//                     accept=".mp4,.mov,.avi,.mkv"
//                     onChange={handleFileChange}
//                     required
//                     style={{ display: "block", marginBottom: "10px" }}
//                 />
//                 <button type="submit" style={{ marginTop: "10px" }}>
//                     Add Video
//                 </button>
//             </form>

//             {/* Video List with Delete Buttons */}
//             <h2>Existing Videos</h2>
//             <ul>
//                 {videos.map((video) => (
//                     <li key={video.id}>
//                         <strong>{video.title}</strong> - {video.description}
//                         <button
//                             onClick={() => handleDeleteVideo(video.id)}
//                             style={{ marginLeft: "10px" }}
//                         >
//                             Delete
//                         </button>
//                     </li>
//                 ))}
//             </ul>
//         </div>
//     );
// };

// export default VideoManagementPage;
