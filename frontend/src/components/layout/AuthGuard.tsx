import { useEffect, useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { useAuthStore } from "@/lib/auth";
import TopNav from "./TopNav";
import { motion, AnimatePresence } from "framer-motion";
import SessionTimeoutManager from "./SessionTimeoutManager";

export default function AuthGuard({ children }: { children: React.ReactNode }) {
  const navigate = useNavigate();
  const location = useLocation();
  const pathname = location.pathname;
  const { token } = useAuthStore();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    // Check if token exists, if not redirect to login
    // Wait until mounted so Zustand persist has time to hydrate from localStorage
    if (mounted && !token) {
      navigate("/login");
    }
  }, [token, navigate, pathname, mounted]);

  if (!mounted || !token) return null;

  return (
    <SessionTimeoutManager>
      <div className="flex flex-col h-screen overflow-hidden w-full bg-transparent relative">
        <TopNav mobileOpen={mobileMenuOpen} setMobileOpen={setMobileMenuOpen} />
        
        <main className="flex-1 overflow-auto relative w-full pt-16 z-10">
          <div className="h-full p-4 md:p-6 lg:p-8 max-w-[1600px] mx-auto w-full">
            <AnimatePresence mode="wait">
              <motion.div
                key={pathname}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                transition={{ duration: 0.3 }}
                className="h-full w-full"
              >
                {children}
              </motion.div>
            </AnimatePresence>
          </div>
        </main>
      </div>
    </SessionTimeoutManager>
  );
}
