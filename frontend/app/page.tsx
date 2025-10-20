"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import Image from "next/image";
import axios from "axios";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

type TabKey = "image" | "text";
type AuthMode = "login" | "register" | "forgot" | "reset";

interface DescriptionResponse {
  description: string;
  seo_score: number;
  seo_factors: string[];
  history_id: string;
  timestamp: string;
  style: string;
  source: string;
  image_url?: string | null;
}



interface HistoryItem {
  id: string;
  timestamp: string;
  source: string;
  style: string;
  summary: string;
  full_description: string;
  image_url?: string | null;
}

interface HistoryDetail extends HistoryItem {
  seo_score: number;
  seo_factors: string[];
}



interface ImageItem {
  id: string;
  file: File;
  previewUrl: string;
}

interface User {
  id: number;
  email: string | null;
  phone_number: string | null;
  created_at: string;
}

interface TokenResponse {
  access_token: string;
  token_type: string;
}

interface ForgotPasswordResponse {
  message: string;
  reset_token?: string;
}

interface MessageResponse {
  message: string;
}

type ToastKind = "error" | "success";

interface ToastState {
  id: number;
  type: ToastKind;
  message: string;
}

const DEFAULT_STYLES = ["Tiếp thị", "Chuyên nghiệp", "Thân thiện", "Kể chuyện"];
const SEO_KEYWORDS = [
  "chất lượng",
  "tươi",
  "ngon",
  "sạch",
  "dinh dưỡng",
  "vitamin",
  "tự nhiên",
];
const SEO_CTA = ["đặt hàng", "mua ngay", "gọi ngay", "liên hệ"];
const SEO_EMOJIS = ["🍎", "🍊", "🍇", "🍌", "🍓", "✨", "💎", "🌟"];

const evaluateSeo = (text: string) => {
  let score = 0;
  const factors: string[] = [];

  const wordCount = text.split(/\s+/).filter(Boolean).length;
  if (wordCount >= 100 && wordCount <= 500) {
    score += 30;
    factors.push("✅ Độ dài phù hợp");
  } else {
    factors.push(`⚠️ Độ dài: ${wordCount} từ (nên 100-500)`);
  }

  const foundKeywords = SEO_KEYWORDS.reduce(
    (acc, keyword) => (text.toLowerCase().includes(keyword.toLowerCase()) ? acc + 1 : acc),
    0
  );
  score += Math.min(foundKeywords * 5, 25);
  factors.push(`✅ Từ khóa: ${foundKeywords}/${SEO_KEYWORDS.length}`);

  const hashtagCount = (text.match(/#/g) ?? []).length;
  if (hashtagCount >= 3) {
    score += 15;
    factors.push("✅ Có hashtags");
  } else {
    factors.push("⚠️ Thiếu hashtags");
  }

  const hasCta = SEO_CTA.some((cta) => text.toLowerCase().includes(cta));
  if (hasCta) {
    score += 15;
    factors.push("✅ Có call-to-action");
  } else {
    factors.push("⚠️ Thiếu call-to-action");
  }

  const hasEmoji = SEO_EMOJIS.some((emoji) => text.includes(emoji));
  if (hasEmoji) {
    score += 15;
    factors.push("✅ Có emoji");
  } else {
    factors.push("⚠️ Thiếu emoji");
  }

  return { score, factors };
};

export default function HomePage() {
  const [activeTab, setActiveTab] = useState<TabKey>("image");
  const [styles, setStyles] = useState<string[]>(DEFAULT_STYLES);
  const [selectedStyle, setSelectedStyle] = useState<string>("Tiếp thị");
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [historyDetail, setHistoryDetail] = useState<HistoryDetail | null>(null);



  const [images, setImages] = useState<ImageItem[]>([]);
  const [selectedImageId, setSelectedImageId] = useState<string | null>(null);
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const previewsRef = useRef<string[]>([]);
  const [cameraActive, setCameraActive] = useState(false);

  const [productInfo, setProductInfo] = useState<string>("");

  const [result, setResult] = useState<DescriptionResponse | null>(null);
  const [seoFactors, setSeoFactors] = useState<string[]>([]);
  const [loading, setLoading] = useState<boolean>(false);

  const [token, setToken] = useState<string | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [authVisible, setAuthVisible] = useState<boolean>(false);
  const [authMode, setAuthMode] = useState<AuthMode>("login");
  const [authLoading, setAuthLoading] = useState<boolean>(false);
  const [authForm, setAuthForm] = useState({ identifier: "", password: "" });
  const [forgotIdentifier, setForgotIdentifier] = useState("");
  const [resetForm, setResetForm] = useState({ identifier: "", token: "", password: "", confirmPassword: "" });
  const [resetTokenHint, setResetTokenHint] = useState<string | null>(null);
  const [toast, setToast] = useState<ToastState | null>(null);
  const [authMessage, setAuthMessage] = useState<{ type: ToastKind; message: string } | null>(null);

  const showToast = useCallback((type: ToastKind, message: string) => {
    const id = Date.now();
    setToast({ id, type, message });
    setTimeout(() => {
      setToast((current) => (current && current.id === id ? null : current));
    }, 4000);
  }, []);

  const clearToast = useCallback(() => setToast(null), []);

  useEffect(() => {
    const storedToken = typeof window !== "undefined" ? sessionStorage.getItem("token") : null;
    if (storedToken) {
      setToken(storedToken);
    }
  }, []);

  const fetchProtectedData = useCallback(async (jwt: string) => {
    try {
      axios.defaults.headers.common.Authorization = `Bearer ${jwt}`;
      const [userRes, historyRes] = await Promise.all([
        axios.get<User>(`${API_BASE_URL}/auth/me`),
        axios.get<HistoryItem[]>(`${API_BASE_URL}/api/history`),
      ]);
      setUser(userRes.data);
      setHistory(historyRes.data);
    } catch (err: any) {
      console.error(err);
      if (err?.response?.status === 401) {
        setToken(null);
        showToast("error", "Phiên đăng nhập đã hết hạn, vui lòng đăng nhập lại.");
      }
    }
  }, [showToast]);

  const stopCamera = useCallback(() => {
    const stream = streamRef.current;
    if (stream) {
      stream.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
    setCameraActive(false);
  }, []);

  useEffect(() => () => stopCamera(), [stopCamera]);

  useEffect(() => {
    if (!cameraActive) {
      return;
    }
    const video = videoRef.current;
    const stream = streamRef.current;
    if (!video || !stream) {
      return;
    }
    video.srcObject = stream;
    video
      .play()
      .catch((err) => {
        console.error(err);
        showToast("error", "Không thể hiển thị camera.");
        stopCamera();
      });
  }, [cameraActive, showToast, stopCamera]);

  useEffect(() => () => {
    previewsRef.current.forEach((url) => URL.revokeObjectURL(url));
    previewsRef.current = [];
  }, []);

  useEffect(() => {
    const fetchPublicData = async () => {
      try {
        const stylesRes = await axios.get<string[]>(`${API_BASE_URL}/api/styles`);
        if (stylesRes.data.length) {
          setStyles(stylesRes.data);
          setSelectedStyle((current) =>
            stylesRes.data.includes(current) ? current : stylesRes.data[0]
          );
        }
      } catch (err) {
        console.error(err);
      }
    };
    void fetchPublicData();
  }, []);

  useEffect(() => {
    if (!token) {
      delete axios.defaults.headers.common.Authorization;
      setUser(null);
      setHistory([]);
      return;
    }
    void fetchProtectedData(token);
  }, [token, fetchProtectedData]);

  const refreshHistory = useCallback(async () => {
    if (!token) {
      return;
    }
    try {
      const { data } = await axios.get<HistoryItem[]>(`${API_BASE_URL}/api/history`);
      setHistory(data);
    } catch (err: any) {
      if (err?.response?.status === 401) {
        setToken(null);
        showToast("error", "Phiên đăng nhập đã hết hạn, vui lòng đăng nhập lại.");
      }
    }
  }, [showToast, token]);

  const handleUnauthorized = useCallback(
    (err: any) => {
      if (err?.response?.status === 401) {
        setToken(null);
        showToast("error", "Phiên đăng nhập đã hết hạn, vui lòng đăng nhập lại.");
        return true;
      }
      return false;
    },
    [showToast]
  );

  const isAuthenticated = Boolean(token && user);



  const startCamera = async () => {
    clearToast();
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: "environment" } });
      streamRef.current = stream;
      setCameraActive(true);
      showToast("success", "Camera đã bật");
    } catch (err) {
      console.error(err);
      showToast("error", "Không thể truy cập camera. Vui lòng kiểm tra quyền truy cập.");
      stopCamera();
      setCameraActive(false);
    }
  };

  const capturePhoto = async () => {
    const video = videoRef.current;
    if (!video) {
      showToast("error", "Không thể chụp ảnh từ camera.");
      return;
    }
    const canvas = document.createElement("canvas");
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const context = canvas.getContext("2d");
    if (!context) {
      showToast("error", "Không thể chụp ảnh từ camera.");
      return;
    }
    context.drawImage(video, 0, 0, canvas.width, canvas.height);
    canvas.toBlob((blob) => {
      if (!blob) {
        showToast("error", "Không thể chụp ảnh từ camera.");
        return;
      }
      const captureFile = new File([blob], `capture-${Date.now()}.png`, { type: "image/png" });
      const previewUrl = URL.createObjectURL(blob);
      previewsRef.current.push(previewUrl);
      const newItem: ImageItem = {
        id: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
        file: captureFile,
        previewUrl,
      };
      setImages((prev) => [...prev, newItem]);
      setSelectedImageId(newItem.id);
      showToast("success", "Đã chụp ảnh từ camera");
    }, "image/png");
    stopCamera();
  };

  const handleImageChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(event.target.files ?? []);
    if (!files.length) {
      return;
    }
    stopCamera();
    clearToast();
    const newItems: ImageItem[] = files.map((file) => {
      const previewUrl = URL.createObjectURL(file);
      previewsRef.current.push(previewUrl);
      return {
        id: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
        file,
        previewUrl,
      };
    });
    setImages((prev) => [...prev, ...newItems]);
    setSelectedImageId(newItems[newItems.length - 1].id);
    showToast("success", newItems.length > 1 ? `Đã thêm ${newItems.length} hình ảnh` : "Đã thêm hình ảnh");
    event.target.value = "";
  };

  const handleSelectImage = (id: string) => {
    setSelectedImageId(id);
  };

  const handleRemoveImage = (id: string) => {
    setImages((prev) => {
      const target = prev.find((item) => item.id === id);
      if (target) {
        URL.revokeObjectURL(target.previewUrl);
        previewsRef.current = previewsRef.current.filter((url) => url !== target.previewUrl);
      }
      const filtered = prev.filter((item) => item.id !== id);
      if (!filtered.length) {
        setSelectedImageId(null);
      } else if (selectedImageId === id) {
        setSelectedImageId(filtered[filtered.length - 1].id);
      }
      return filtered;
    });
  };

  const handleImageSubmit = async () => {
    const imageToSubmit = activeImage;
    if (!imageToSubmit) {
      showToast("error", "Vui lòng thêm ít nhất một hình ảnh hợp lệ.");
      return;
    }
    setLoading(true);
    clearToast();
    try {
      const formData = new FormData();
      formData.append("file", imageToSubmit.file);
      formData.append("style", selectedStyle);

      const { data } = await axios.post<DescriptionResponse>(
        `${API_BASE_URL}/api/descriptions/image`,
        formData,
        { headers: { "Content-Type": "multipart/form-data" } }
      );

      setResult(data);
      setSeoFactors(data.seo_factors);
      if (token) {
        await refreshHistory();
        showToast("success", "Đã tạo mô tả từ hình ảnh và lưu vào lịch sử");
      } else {
        showToast("success", "Đã tạo mô tả từ hình ảnh. Đăng nhập để lưu lịch sử!");
      }
    } catch (err: any) {
      if (handleUnauthorized(err)) {
        return;
      }
      const detail = err?.response?.data?.detail ?? "Không thể tạo mô tả";
      showToast("error", detail);
    } finally {
      setLoading(false);
    }
  };

  const handleTextSubmit = async () => {
    if (!productInfo.trim()) {
      showToast("error", "Vui lòng nhập thông tin sản phẩm");
      return;
    }
    setLoading(true);
    clearToast();
    try {
      const { data } = await axios.post<DescriptionResponse>(`${API_BASE_URL}/api/descriptions/text`, {
        product_info: productInfo,
        style: selectedStyle,
      });
      setResult(data);
      setSeoFactors(data.seo_factors);
      if (token) {
        await refreshHistory();
        showToast("success", "Đã tạo mô tả từ văn bản và lưu vào lịch sử");
      } else {
        showToast("success", "Đã tạo mô tả từ văn bản. Đăng nhập để lưu lịch sử!");
      }
    } catch (err: any) {
      if (handleUnauthorized(err)) {
        return;
      }
      const detail = err?.response?.data?.detail ?? "Không thể tạo mô tả";
      showToast("error", detail);
    } finally {
      setLoading(false);
    }
  };





  const handleAuthSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (authMode !== "login" && authMode !== "register") {
      return;
    }
    setAuthLoading(true);
    clearToast();
    setAuthMessage(null);
    try {
      const identifier = authForm.identifier.trim();
      const password = authForm.password.trim();
      if (!identifier || !password) {
        const message = "Vui lòng nhập đầy đủ email/số điện thoại và mật khẩu hợp lệ.";
        setAuthMessage({ type: "error", message });
        showToast("error", message);
        setAuthLoading(false);
        return;
      }
      const url = authMode === "login" ? "/auth/login" : "/auth/register";
      const { data } = await axios.post<TokenResponse>(`${API_BASE_URL}${url}`, {
        identifier,
        password,
      });
      const newToken = data.access_token;
      setToken(newToken);
      if (typeof window !== "undefined") {
        sessionStorage.setItem("token", newToken);
      }
      await fetchProtectedData(newToken);
      setAuthMessage({
        type: "success",
        message: authMode === "login" ? "Đăng nhập thành công" : "Đăng ký thành công",
      });
      setAuthForm({ identifier: "", password: "" });
      showToast("success", authMode === "login" ? "Đăng nhập thành công" : "Đăng ký thành công");
      setTimeout(() => {
        setAuthVisible(false);
        setAuthMessage(null);
      }, 1200);
    } catch (err: any) {
      let detail = "Không thể xác thực";
      
      // Xử lý các loại error response khác nhau
      if (err?.response?.data?.detail) {
        const errorDetail = err.response.data.detail;
        
        // Nếu detail là array (validation errors từ Pydantic)
        if (Array.isArray(errorDetail)) {
          detail = errorDetail.map((e: any) => e.msg || e.message).join(", ");
        } 
        // Nếu detail là string
        else if (typeof errorDetail === "string") {
          detail = errorDetail;
        }
        // Nếu detail là object
        else if (typeof errorDetail === "object") {
          detail = errorDetail.msg || errorDetail.message || JSON.stringify(errorDetail);
        }
      }
      
      setAuthMessage({ type: "error", message: detail });
      showToast("error", detail);
    } finally {
      setAuthLoading(false);
    }
  };

  const handleForgotSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setAuthLoading(true);
    clearToast();
    setAuthMessage(null);
    setResetTokenHint(null);
    try {
      const identifier = forgotIdentifier.trim();
      if (!identifier) {
        const message = "Vui lòng nhập email hoặc số điện thoại đã đăng ký.";
        setAuthMessage({ type: "error", message });
        showToast("error", message);
        setAuthLoading(false);
        return;
      }
      const { data } = await axios.post<ForgotPasswordResponse>(
        `${API_BASE_URL}/auth/forgot-password`,
        { identifier }
      );
      setAuthMessage({ type: "success", message: data.message });
      showToast("success", data.message);
      setForgotIdentifier("");
      if (data.reset_token) {
        setResetTokenHint(data.reset_token);
        setResetForm({ identifier, token: data.reset_token, password: "", confirmPassword: "" });
        setAuthMode("reset");
      }
    } catch (err: any) {
      let detail = "Không thể tạo mã đặt lại";
      
      if (err?.response?.data?.detail) {
        const errorDetail = err.response.data.detail;
        if (Array.isArray(errorDetail)) {
          detail = errorDetail.map((e: any) => e.msg || e.message).join(", ");
        } else if (typeof errorDetail === "string") {
          detail = errorDetail;
        } else if (typeof errorDetail === "object") {
          detail = errorDetail.msg || errorDetail.message || JSON.stringify(errorDetail);
        }
      }
      
      setAuthMessage({ type: "error", message: detail });
      showToast("error", detail);
    } finally {
      setAuthLoading(false);
    }
  };

  const handleResetSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setAuthLoading(true);
    clearToast();
    setAuthMessage(null);
    try {
      const identifier = resetForm.identifier.trim();
      const tokenValue = resetForm.token.trim();
      const password = resetForm.password.trim();
      const confirm = resetForm.confirmPassword.trim();
      if (!identifier || !tokenValue || !password) {
        const message = "Vui lòng nhập đầy đủ email/số điện thoại, mã đặt lại và mật khẩu mới.";
        setAuthMessage({ type: "error", message });
        showToast("error", message);
        setAuthLoading(false);
        return;
      }
      if (password !== confirm) {
        const message = "Mật khẩu xác nhận không khớp.";
        setAuthMessage({ type: "error", message });
        showToast("error", message);
        setAuthLoading(false);
        return;
      }
      const { data } = await axios.post<MessageResponse>(`${API_BASE_URL}/auth/reset-password`, {
        identifier,
        token: tokenValue,
        new_password: password,
      });
      setAuthMessage({ type: "success", message: data.message });
      showToast("success", data.message);
      setResetForm({ identifier: "", token: "", password: "", confirmPassword: "" });
      setResetTokenHint(null);
      setAuthMode("login");
      setAuthForm({ identifier, password: "" });
    } catch (err: any) {
      let detail = "Không thể đặt lại mật khẩu";
      
      if (err?.response?.data?.detail) {
        const errorDetail = err.response.data.detail;
        if (Array.isArray(errorDetail)) {
          detail = errorDetail.map((e: any) => e.msg || e.message).join(", ");
        } else if (typeof errorDetail === "string") {
          detail = errorDetail;
        } else if (typeof errorDetail === "object") {
          detail = errorDetail.msg || errorDetail.message || JSON.stringify(errorDetail);
        }
      }
      
      setAuthMessage({ type: "error", message: detail });
      showToast("error", detail);
    } finally {
      setAuthLoading(false);
    }
  };

  const changeAuthMode = (mode: AuthMode) => {
    setAuthMode(mode);
    setAuthMessage(null);
    setAuthLoading(false);
    if (mode !== "reset") {
      setResetTokenHint(null);
      setResetForm({ identifier: "", token: "", password: "", confirmPassword: "" });
    }
    if (mode !== "forgot") {
      setForgotIdentifier("");
    }
  };

  const handleLogout = () => {
    setToken(null);
    if (typeof window !== "undefined") {
      sessionStorage.removeItem("token");
    }
    setUser(null);
    setHistory([]);
    setResult(null);
    stopCamera();
    showToast("success", "Đã đăng xuất");
  };

  const activeImage = useMemo(() => {
    if (!images.length) {
      return null;
    }
    if (selectedImageId) {
      const found = images.find((item) => item.id === selectedImageId);
      if (found) {
        return found;
      }
    }
    return images[0];
  }, [images, selectedImageId]);

  const seoScoreClass = useMemo(() => {
    if (!result) return "";
    if (result.seo_score >= 70) return "high";
    if (result.seo_score >= 40) return "medium";
    return "low";
  }, [result]);

  return (
    <div className="app-container">
      <div className="glass-panel">
        <header style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 16 }}>
          <div>
            <h1> AI Mô Tả Sản Phẩm Trái Cây </h1>
            <p style={{ color: "var(--text-secondary)", marginBottom: 32 }}>
               Từ hình ảnh đến mô tả hoàn hảo |  Nhiều phong cách viết |  Tối ưu SEO tự động
            </p>
          </div>
          <div>
            {isAuthenticated ? (
              <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: 8 }}>
                <span style={{ color: "var(--text-secondary)" }}>
                  {user?.email || user?.phone_number}
                </span>
                <button className="secondary-button" onClick={handleLogout}>
                  Đăng xuất
                </button>
              </div>
            ) : (
              <button
                className="primary-button"
                onClick={() => {
                  changeAuthMode("login");
                  setAuthForm({ identifier: "", password: "" });
                  setAuthVisible(true);
                }}
              >
                Đăng nhập / Đăng ký
              </button>
            )}
          </div>
        </header>

        <div className="section">
          <label htmlFor="style-select" style={{ fontWeight: 600, display: "block", marginBottom: 12 }}>
             Phong cách viết
          </label>
          <select
            id="style-select"
            value={selectedStyle}
            onChange={(event) => setSelectedStyle(event.target.value)}
          >
            {styles.map((style) => (
              <option key={style} value={style}>
                {style}
              </option>
            ))}
          </select>
        </div>

        <div className="section">
          <div className="tab-group">
            <button
              className={`tab-button ${activeTab === "image" ? "active" : ""}`}
              onClick={() => setActiveTab("image")}
            >
               Phân tích hình ảnh
            </button>
            <button
              className={`tab-button ${activeTab === "text" ? "active" : ""}`}
              onClick={() => setActiveTab("text")}
            >
               Tạo từ mô tả text
            </button>
          </div>
        </div>

        {activeTab === "image" && (
          <div className="section">
            <div className="grid two-column">
              <div className="card">
                <h2> Tải hoặc chụp hình ảnh sản phẩm</h2>
                <p style={{ color: "var(--text-secondary)" }}>
                  Hỗ trợ định dạng JPG, JPEG, PNG (dưới 5MB) hoặc dùng camera trực tiếp
                </p>
                <input type="file" accept="image/*" multiple onChange={handleImageChange} />

                <div style={{ marginTop: 20, display: "flex", flexDirection: "column", gap: 12 }}>
                  {cameraActive ? (
                    <video
                      ref={videoRef}
                      style={{ width: "100%", borderRadius: 20, background: "#000" }}
                      autoPlay
                      playsInline
                      muted
                    />
                  ) : null}

                  {!cameraActive && activeImage && (
                    <div>
                      <Image
                        src={activeImage.previewUrl}
                        alt="Xem trước"
                        width={600}
                        height={400}
                        style={{ borderRadius: 20, width: "100%", height: "auto" }}
                        unoptimized
                      />
                    </div>
                  )}

                  {!cameraActive && !activeImage && (
                    <div
                      style={{
                        border: "1px dashed rgba(0,0,0,0.15)",
                        borderRadius: 20,
                        padding: 24,
                        textAlign: "center",
                        color: "var(--text-secondary)",
                      }}
                    >
                      Chưa có hình ảnh nào, hãy tải lên hoặc dùng camera.
                    </div>
                  )}

                  {images.length > 0 && (
                    <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
                      {images.map((item) => (
                        <div
                          key={item.id}
                          style={{
                            position: "relative",
                            borderRadius: 16,
                            overflow: "hidden",
                            border:
                              item.id === activeImage?.id
                                ? "2px solid var(--accent-orange)"
                                : "2px solid transparent",
                            boxShadow: "0 10px 24px rgba(0,0,0,0.12)",
                            cursor: "pointer",
                          }}
                          onClick={() => handleSelectImage(item.id)}
                        >
                          <button
                            type="button"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleRemoveImage(item.id);
                            }}
                            style={{
                              position: "absolute",
                              top: 6,
                              right: 6,
                              background: "rgba(0,0,0,0.55)",
                              color: "#fff",
                              border: "none",
                              borderRadius: "50%",
                              width: 28,
                              height: 28,
                              display: "flex",
                              alignItems: "center",
                              justifyContent: "center",
                              cursor: "pointer",
                            }}
                            aria-label="Xóa hình ảnh"
                          >
                            ✕
                          </button>
                          <Image
                            src={item.previewUrl}
                            alt="Hình ảnh đã chọn"
                            width={140}
                            height={140}
                            style={{ objectFit: "cover", width: 140, height: 140 }}
                            unoptimized
                          />
                        </div>
                      ))}
                    </div>
                  )}

                  <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
                    {!cameraActive ? (
                      <button className="secondary-button" onClick={startCamera}>
                         Mở camera
                      </button>
                    ) : (
                      <>
                        <button className="primary-button" onClick={capturePhoto}>
                           Chụp ảnh
                        </button>
                        <button className="secondary-button" onClick={stopCamera}>
                           Đóng camera
                        </button>
                      </>
                    )}
                  </div>
                </div>

                <button
                  className="primary-button"
                  style={{ marginTop: 24, width: "100%" }}
                  onClick={handleImageSubmit}
                  disabled={loading}
                >
                  {loading ? (
                    <span style={{ display: "inline-flex", alignItems: "center", gap: 10 }}>
                      <span className="loader" /> Đang tạo mô tả...
                    </span>
                  ) : (
                    " AI tạo mô tả ngay"
                  )}
                </button>
              </div>

              {result && (
                <div className="card">
                  <h2>✨ Kết quả</h2>
                  <p style={{ whiteSpace: "pre-line", lineHeight: 1.7 }}>{result.description}</p>
                  <div style={{ marginTop: 24 }}>
                    <span className={`seo-pill ${seoScoreClass}`}>
                       Điểm SEO: {result.seo_score}/100
                    </span>
                  </div>
                  <ul style={{ marginTop: 16, paddingLeft: 20 }}>
                    {seoFactors.map((factor) => (
                      <li key={factor}>{factor}</li>
                    ))}
                  </ul>
                  <div style={{ marginTop: 24, display: "flex", gap: 12, flexWrap: "wrap" }}>
                    <button
                      className="secondary-button"
                      onClick={() => navigator.clipboard.writeText(result.description)}
                    >
                       Sao chép
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {activeTab === "text" && (
          <div className="section">
            <div className="card" style={{ marginBottom: 24 }}>
              <h2>📝 Nhập thông tin sản phẩm</h2>
              <textarea
                rows={7}
                placeholder="Ví dụ: Táo Fuji nhập khẩu Nhật Bản, quả to, màu đỏ tươi, ngọt giòn"
                value={productInfo}
                onChange={(event) => setProductInfo(event.target.value)}
              />
              <button
                className="primary-button"
                style={{ marginTop: 20, width: "100%" }}
                onClick={handleTextSubmit}
                disabled={loading}
              >
                {loading ? (
                  <span style={{ display: "inline-flex", alignItems: "center", gap: 10 }}>
                    <span className="loader" /> Đang tạo mô tả...
                  </span>
                ) : (
                  "✨ Tạo mô tả chi tiết"
                )}
              </button>
            </div>

            {result && (
              <div className="card">
                <h2> Kết quả</h2>
                <p style={{ whiteSpace: "pre-line", lineHeight: 1.7 }}>{result.description}</p>
                <div style={{ marginTop: 24 }}>
                  <span className={`seo-pill ${seoScoreClass}`}>
                     Điểm SEO: {result.seo_score}/100
                  </span>
                </div>
                <ul style={{ marginTop: 16, paddingLeft: 20 }}>
                  {seoFactors.map((factor) => (
                    <li key={factor}>{factor}</li>
                  ))}
                </ul>
                <div style={{ marginTop: 24, display: "flex", gap: 12, flexWrap: "wrap" }}>
                  <button
                    className="secondary-button"
                    onClick={() => navigator.clipboard.writeText(result.description)}
                  >
                     Sao chép
                  </button>
                </div>
              </div>
            )}
          </div>
        )}



        <div className="section">
          <h2>📜 Lịch sử mô tả</h2>
          {!isAuthenticated ? (
            <div style={{ textAlign: "center", padding: "40px 20px" }}>
              <p style={{ color: "var(--text-secondary)", marginBottom: 16 }}>
                🔒 Đăng nhập để xem và lưu lịch sử mô tả của bạn
              </p>
              <button
                className="primary-button"
                onClick={() => {
                  setAuthVisible(true);
                  setAuthMode("login");
                }}
              >
                Đăng nhập ngay
              </button>
            </div>
          ) : history.length === 0 ? (
            <p style={{ color: "var(--text-secondary)" }}>Chưa có lịch sử.</p>
          ) : (
            <div className="history-grid">
              {history.map((item) => (
                <div key={item.id} className="history-item">
                  <strong>{new Date(item.timestamp).toLocaleString()}</strong>
                  <span style={{ color: "var(--text-secondary)" }}>
                    Nguồn: {item.source === "image" ? "Hình ảnh" : "Văn bản"}
                  </span>
                  <span style={{ color: "var(--accent-orange)", fontWeight: 600 }}>
                    Phong cách: {item.style}
                  </span>
                  {item.image_url && (
                    <div
                      style={{
                        marginTop: 12,
                        borderRadius: 16,
                        overflow: "hidden",
                        border: "1px solid rgba(0,0,0,0.05)",
                        position: "relative",
                        width: "100%",
                        height: 160,
                      }}
                    >
                      <Image
                        src={`${API_BASE_URL}${item.image_url}`}
                        alt="Ảnh mô tả"
                        fill
                        sizes="(max-width: 768px) 100vw, 320px"
                        style={{ objectFit: "cover" }}
                      />
                    </div>
                  )}
                  <p style={{ color: "var(--text-secondary)", margin: 0 }}>{item.summary}</p>
                  <button
                    className="secondary-button"
                    onClick={() => {
                      const evaluation = evaluateSeo(item.full_description);
                      setActiveTab("text");
                      setHistoryDetail({
                        ...item,
                        seo_score: evaluation.score,
                        seo_factors: evaluation.factors,
                      });
                      setResult({
                        description: item.full_description,
                        seo_score: evaluation.score,
                        seo_factors: evaluation.factors,
                        history_id: item.id,
                        timestamp: item.timestamp,
                        style: item.style,
                        source: item.source,
                        image_url: item.image_url ?? null,
                      });
                      setSeoFactors(evaluation.factors);
                    }}
                  >
                    Xem chi tiết
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        <footer style={{ marginTop: 48, textAlign: "center", color: "var(--text-secondary)" }}>
          <p> Mẹo: thử nhiều phong cách viết và kiểm tra điểm SEO để tối ưu nội dung.</p>
        </footer>
      </div>

      {toast && (
        <div
          style={{
            position: "fixed",
            top: 24,
            right: 24,
            zIndex: 1100,
            minWidth: 260,
            maxWidth: 360,
            padding: "14px 18px",
            borderRadius: 18,
            background: toast.type === "error" ? "#F56565" : "#38A169",
            color: "#fff",
            boxShadow: "0 16px 40px rgba(0,0,0,0.2)",
            fontWeight: 600,
            lineHeight: 1.4,
          }}
        >
          {toast.message}
        </div>
      )}

      {historyDetail && (
        <div
          style={{
            position: "fixed",
            inset: 0,
            background: "rgba(0,0,0,0.55)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            padding: 16,
            zIndex: 1000,
          }}
          onClick={() => setHistoryDetail(null)}
        >
          <div
            style={{
              width: "100%",
              maxWidth: 720,
              background: "#fff",
              borderRadius: 28,
              padding: 32,
              boxShadow: "0 32px 80px rgba(0,0,0,0.2)",
              display: "flex",
              flexDirection: "column",
              gap: 20,
              maxHeight: "90vh",
              overflowY: "auto",
            }}
            onClick={(event) => event.stopPropagation()}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <div>
                <h2 style={{ margin: "0 0 8px" }}>Chi tiết mô tả</h2>
                <p style={{ margin: 0, color: "var(--text-secondary)" }}>
                  {new Date(historyDetail.timestamp).toLocaleString()} • Nguồn: {historyDetail.source === "image" ? "Hình ảnh" : "Văn bản"}
                </p>
                <p style={{ margin: "4px 0 0", color: "var(--accent-orange)", fontWeight: 600 }}>
                  Phong cách: {historyDetail.style}
                </p>
              </div>
              <button className="secondary-button" onClick={() => setHistoryDetail(null)}>
                Đóng
              </button>
            </div>
            <div>
              <h3 style={{ marginTop: 0 }}>Điểm SEO: {historyDetail.seo_score}/100</h3>
              <ul style={{ paddingLeft: 20, color: "var(--text-secondary)" }}>
                {historyDetail.seo_factors.map((factor) => (
                  <li key={factor}>{factor}</li>
                ))}
              </ul>
            </div>
            {historyDetail.image_url && (
              <div
                style={{
                  borderRadius: 24,
                  overflow: "hidden",
                  border: "1px solid rgba(0,0,0,0.08)",
                  position: "relative",
                  width: "100%",
                  height: "min(360px, 60vh)",
                }}
              >
                <Image
                  src={`${API_BASE_URL}${historyDetail.image_url}`}
                  alt="Ảnh mô tả"
                  fill
                  sizes="(max-width: 768px) 100vw, 640px"
                  style={{ objectFit: "cover" }}
                />
              </div>
            )}
            <div
              style={{
                background: "#f8f9fb",
                padding: 24,
                borderRadius: 20,
                lineHeight: 1.7,
                color: "var(--text-primary)",
                whiteSpace: "pre-line",
              }}
            >
              {historyDetail.full_description}
            </div>
            <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
              <button
                className="secondary-button"
                onClick={() => navigator.clipboard.writeText(historyDetail.full_description)}
              >
                📋 Sao chép
              </button>
            </div>
          </div>
        </div>
      )}



      {authVisible && (
        <div
          style={{
            position: "fixed",
            inset: 0,
            background: "rgba(0,0,0,0.45)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            padding: 16,
            zIndex: 1000,
          }}
        >
          <div
            style={{
              width: "100%",
              maxWidth: 420,
              background: "#fff",
              borderRadius: 24,
              padding: 32,
              boxShadow: "0 24px 60px rgba(0,0,0,0.12)",
              display: "flex",
              flexDirection: "column",
              gap: 16,
              position: "relative",
            }}
          >
            <button
              type="button"
              onClick={() => {
                setAuthVisible(false);
                changeAuthMode("login");
                setAuthForm({ identifier: "", password: "" });
                setAuthMessage(null);
              }}
              style={{
                position: "absolute",
                top: 16,
                right: 16,
                background: "rgba(0,0,0,0.08)",
                color: "var(--text-primary)",
                border: "none",
                borderRadius: "50%",
                width: 32,
                height: 32,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                cursor: "pointer",
                fontSize: 20,
                fontWeight: 600,
                transition: "all 0.2s",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.background = "rgba(0,0,0,0.15)";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.background = "rgba(0,0,0,0.08)";
              }}
              aria-label="Đóng"
            >
              ✕
            </button>
            <h2 style={{ margin: 0, textAlign: "center" }}>
              {authMode === "login"
                ? "Đăng nhập tài khoản"
                : authMode === "register"
                ? "Đăng ký tài khoản mới"
                : authMode === "forgot"
                ? "Khôi phục mật khẩu"
                : "Đặt lại mật khẩu"}
            </h2>
            {authMessage && (
              <div
                className="error-box"
                style={{
                  borderColor: authMessage.type === "success" ? "#38A169" : undefined,
                  background: authMessage.type === "success" ? "rgba(56,161,105,0.12)" : undefined,
                  color: authMessage.type === "success" ? "#276749" : undefined,
                }}
              >
                {authMessage.message}
              </div>
            )}
            {authMode === "reset" && resetTokenHint && (
              <div
                style={{
                  border: "1px solid rgba(56,161,105,0.45)",
                  background: "rgba(56,161,105,0.12)",
                  color: "#276749",
                  borderRadius: 16,
                  padding: 14,
                  textAlign: "center",
                  fontWeight: 600,
                  wordBreak: "break-all",
                }}
              >
                <div>Mã đặt lại của bạn:</div>
                <code style={{ display: "block", marginTop: 8 }}>{resetTokenHint}</code>
              </div>
            )}
            {(authMode === "login" || authMode === "register") && (
              <form onSubmit={handleAuthSubmit} style={{ display: "flex", flexDirection: "column", gap: 16 }}>
                <input
                  type="text"
                  placeholder="Email hoặc Số điện thoại"
                  value={authForm.identifier}
                  onChange={(event) => setAuthForm((prev) => ({ ...prev, identifier: event.target.value }))}
                  required
                />
                <input
                  type="password"
                  placeholder="Mật khẩu"
                  value={authForm.password}
                  onChange={(event) => setAuthForm((prev) => ({ ...prev, password: event.target.value }))}
                  required
                  minLength={6}
                />
                <button className="primary-button" type="submit" disabled={authLoading}>
                  {authLoading ? "Đang xử lý..." : authMode === "login" ? "Đăng nhập" : "Đăng ký"}
                </button>
              </form>
            )}
            {authMode === "forgot" && (
              <form onSubmit={handleForgotSubmit} style={{ display: "flex", flexDirection: "column", gap: 16 }}>
                <input
                  type="text"
                  placeholder="Nhập email hoặc số điện thoại đã đăng ký"
                  value={forgotIdentifier}
                  onChange={(event) => setForgotIdentifier(event.target.value)}
                  required
                />
                <button className="primary-button" type="submit" disabled={authLoading}>
                  {authLoading ? "Đang xử lý..." : "Gửi mã đặt lại"}
                </button>
              </form>
            )}
            {authMode === "reset" && (
              <form onSubmit={handleResetSubmit} style={{ display: "flex", flexDirection: "column", gap: 16 }}>
                <input
                  type="text"
                  placeholder="Email hoặc Số điện thoại"
                  value={resetForm.identifier}
                  onChange={(event) => setResetForm((prev) => ({ ...prev, identifier: event.target.value }))}
                  required
                />
                <input
                  type="text"
                  placeholder="Mã đặt lại"
                  value={resetForm.token}
                  onChange={(event) => setResetForm((prev) => ({ ...prev, token: event.target.value }))}
                  required
                />
                <input
                  type="password"
                  placeholder="Mật khẩu mới"
                  value={resetForm.password}
                  onChange={(event) => setResetForm((prev) => ({ ...prev, password: event.target.value }))}
                  required
                  minLength={6}
                />
                <input
                  type="password"
                  placeholder="Nhập lại mật khẩu mới"
                  value={resetForm.confirmPassword}
                  onChange={(event) => setResetForm((prev) => ({ ...prev, confirmPassword: event.target.value }))}
                  required
                  minLength={6}
                />
                <button className="primary-button" type="submit" disabled={authLoading}>
                  {authLoading ? "Đang xử lý..." : "Đặt lại mật khẩu"}
                </button>
              </form>
            )}
            <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
              {authMode === "login" && (
                <>
                  <button className="secondary-button" type="button" onClick={() => changeAuthMode("register")} style={{ flex: 1 }}>
                     Đăng ký tài khoản
                  </button>
                  <button className="secondary-button" type="button" onClick={() => changeAuthMode("forgot")} style={{ flex: 1 }}>
                    Quên mật khẩu
                  </button>
                </>
              )}
              {authMode === "register" && (
                <button className="secondary-button" type="button" onClick={() => changeAuthMode("login")} style={{ width: "100%" }}>
                  Đã có tài khoản? Đăng nhập
                </button>
              )}
              {(authMode === "forgot" || authMode === "reset") && (
                <button className="secondary-button" type="button" onClick={() => changeAuthMode("login")} style={{ width: "100%" }}>
                  Quay lại đăng nhập
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
