import { Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function Home() {
  const { user } = useAuth()

  return (
    <div className="min-h-screen bg-obsidian overflow-hidden">
      {/* Background effects */}
      <div className="fixed inset-0 bg-grid-pattern opacity-40 pointer-events-none" />
      <div className="fixed top-0 left-1/2 -translate-x-1/2 w-[900px] h-[600px] 
                      bg-plasma/10 rounded-full blur-[120px] pointer-events-none" />
      <div className="fixed bottom-0 right-0 w-[400px] h-[400px] 
                      bg-ice/5 rounded-full blur-[100px] pointer-events-none" />

      {/* Nav */}
      <nav className="relative z-10 flex items-center justify-between px-8 py-6 max-w-7xl mx-auto">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-plasma rounded-lg flex items-center justify-center">
            <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
            </svg>
          </div>
          <span className="font-bold text-xl tracking-tight text-white">SupportAI</span>
        </div>
        <div className="flex items-center gap-4">
          {user ? (
            <Link to="/dashboard" className="btn-primary text-sm">Dashboard</Link>
          ) : (
            <>
              <Link to="/login" className="text-mist/60 hover:text-mist transition-colors text-sm font-medium">Sign In</Link>
              <Link to="/register" className="btn-primary text-sm">Get Started</Link>
            </>
          )}
        </div>
      </nav>

      {/* Hero */}
      <main className="relative z-10 max-w-7xl mx-auto px-8 pt-24 pb-32">
        <div className="text-center max-w-4xl mx-auto">
          {/* Badge */}
          <div className="inline-flex items-center gap-2 bg-plasma/10 border border-plasma/20 
                          rounded-full px-4 py-1.5 text-sm text-neon mb-8 animate-fade-in">
            <span className="w-2 h-2 bg-neon rounded-full animate-pulse-slow" />
            AI-powered customer support — instant deployment
          </div>

          {/* Headline */}
          <h1 className="text-6xl md:text-7xl font-bold text-white leading-[1.05] tracking-tight mb-6 animate-slide-up">
            Create Your<br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-plasma via-neon to-ice glow-text">
              AI Support Bot
            </span><br />
            in Minutes
          </h1>

          <p className="text-xl text-mist/50 max-w-2xl mx-auto mb-12 leading-relaxed animate-fade-in">
            Upload your docs. Train your bot. Share a link. 
            Your customers get instant, accurate answers 24/7 — 
            powered by cutting-edge LLMs.
          </p>

          {/* CTAs */}
          <div className="flex items-center justify-center gap-4 flex-wrap animate-fade-in">
            <Link to="/register" className="btn-primary text-lg px-8 py-4 inline-flex items-center gap-2 group">
              Get Started Free
              <svg className="w-4 h-4 group-hover:translate-x-1 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3" />
              </svg>
            </Link>
            <Link to="/login" className="btn-ghost text-lg px-8 py-4">
              Sign In
            </Link>
          </div>
        </div>

        {/* Features */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-32">
          {[
            {
              icon: (
                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                </svg>
              ),
              title: "Upload & Train",
              desc: "Drop your PDF or TXT files. We extract, chunk, and embed your knowledge automatically."
            },
            {
              icon: (
                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
                </svg>
              ),
              title: "Share Your Link",
              desc: "Get a unique chatbot URL. Embed it anywhere or share directly with your customers."
            },
            {
              icon: (
                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                </svg>
              ),
              title: "Data Isolation",
              desc: "Each business has fully isolated embeddings. Zero cross-tenant data leakage."
            }
          ].map((feature, i) => (
            <div key={i} className="glass-card p-6 group hover:border-plasma/20 transition-all duration-300">
              <div className="w-12 h-12 bg-plasma/10 rounded-xl flex items-center justify-center text-neon mb-4 
                              group-hover:bg-plasma/20 transition-colors">
                {feature.icon}
              </div>
              <h3 className="text-white font-bold text-lg mb-2">{feature.title}</h3>
              <p className="text-mist/50 text-sm leading-relaxed">{feature.desc}</p>
            </div>
          ))}
        </div>

        {/* Bottom CTA */}
        <div className="mt-24 text-center glass-card p-12 relative overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-r from-plasma/5 via-transparent to-ice/5" />
          <div className="relative z-10">
            <h2 className="text-4xl font-bold text-white mb-4">Ready to automate your support?</h2>
            <p className="text-mist/50 mb-8">Set up your AI chatbot in under 5 minutes.</p>
            <Link to="/register" className="btn-primary text-lg px-10 py-4 inline-block">
              Start for Free
            </Link>
          </div>
        </div>
      </main>
    </div>
  )
}
