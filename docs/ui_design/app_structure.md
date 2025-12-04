# App Structure Explanation

## ✅ You're Doing It Right!

Your app is correctly using **React Router v6** with `RouterProvider`, which is the modern, recommended approach.

---

## 📁 How Your App Works

### Entry Point: `main.tsx`

```tsx
<StrictMode>
  <AuthProvider>
    <RouterProvider router={router} />
  </AuthProvider>
</StrictMode>
```

This is the root of your application. It:

1. Wraps everything in `AuthProvider` for authentication
2. Uses `RouterProvider` with your router configuration
3. **Does NOT use App.tsx** - the router handles everything

### Router: `router.tsx`

Defines all your routes:

```tsx
/login          → LoginPage
/               → ProtectedLayout
  ├─ / (index)  → HomePage
  ├─ /task      → TaskPage
  └─ /calendar  → CalendarPage
```

### ProtectedLayout: `routes/protected.tsx`

This is your main layout for authenticated users. It:

- Checks if user is authenticated
- Shows a loading spinner while checking
- Redirects to `/login` if not authenticated
- Shows navigation bar with:
  - App logo
  - Navigation links (Home, Tasks, Calendar)
  - **Dark mode toggle** (☀️/🌙)
  - User welcome message
  - Logout button
- Renders child routes with `<Outlet />`

---

## 🎨 Theme & Styling

### CSS Files

1. **`index.css`** - Global base styles (reset, fonts)
2. **`App.css`** - Your custom theme (colors, components)

Both are imported in `main.tsx`:

```tsx
import "./index.css";
import "./App.css"; // Theme styles
```

### Dark Mode

Dark mode is now in `ProtectedLayout`:

- Toggle button in the navigation bar (☀️/🌙)
- Saves preference to `localStorage`
- Automatically loads saved preference on mount
- Uses the theme from `App.css`

**How it works:**

```tsx
// Toggle
document.documentElement.classList.toggle("dark");

// Save preference
localStorage.setItem("darkMode", "true");
```

---

## 🗂️ File Structure

```
src/
├── main.tsx              ← Entry point (renders RouterProvider)
├── router.tsx            ← Route configuration
├── index.css             ← Global base styles
├── App.css               ← Theme (colors, component classes)
│
├── contexts/
│   └── AuthContext.tsx   ← Authentication state
│
├── routes/
│   ├── protected.tsx     ← Main layout (nav, dark mode toggle)
│   ├── home.tsx          ← Home page
│   ├── tasks.tsx         ← Tasks page
│   └── calendar.tsx      ← Calendar page
│
└── features/
    └── login/
        └── index.tsx     ← Login page
```

---

## ❌ Removed Files

### `App.tsx` - DELETED ✅

**Why?** It was the old Vite demo file and wasn't being used in the router setup.

With React Router v6's `RouterProvider`, you don't need a traditional `App.tsx`. Your `router.tsx` + route components replace it.

---

## 🚀 How Routing Works

### 1. User visits `/`

```
main.tsx
  → router.tsx checks route "/"
    → ProtectedLayout checks authentication
      → If authenticated: shows HomePage in <Outlet />
      → If not: redirects to /login
```

### 2. User visits `/task`

```
main.tsx
  → router.tsx checks route "/task"
    → ProtectedLayout checks authentication
      → If authenticated: shows TaskPage in <Outlet />
      → If not: redirects to /login
```

### 3. User visits `/login`

```
main.tsx
  → router.tsx checks route "/login"
    → Shows LoginPage (no ProtectedLayout wrapper)
```

---

## 🎯 Key Concepts

### No More App.tsx

**Traditional React:**

```tsx
// main.tsx
<App />;

// App.tsx
function App() {
  return <Router>...</Router>;
}
```

**Modern React Router v6:**

```tsx
// main.tsx
<RouterProvider router={router} />

// router.tsx
export const router = createBrowserRouter([...]);
```

### Layout Routes

`ProtectedLayout` is a **layout route** that:

- Wraps multiple child routes
- Provides shared UI (navigation bar)
- Handles shared logic (authentication, dark mode)
- Renders children via `<Outlet />`

This is much cleaner than passing props or using context for layouts!

---

## 🔄 Common Patterns

### Adding a New Page

1. Create the component:

```tsx
// src/routes/profile.tsx
export default function ProfilePage() {
  return <div>Profile</div>;
}
```

2. Add to router:

```tsx
// router.tsx
import ProfilePage from "./routes/profile";

children: [
  // ... existing routes
  {
    path: "profile",
    element: <ProfilePage />,
  },
];
```

3. Add navigation link in `ProtectedLayout`:

```tsx
<a href="/profile" className="...">
  Profile
</a>
```

### Adding Dark Mode to Login Page

If you want dark mode on the login page too:

```tsx
// features/login/index.tsx
import { useEffect, useState } from "react";

export default function LoginPage() {
  const [isDark, setIsDark] = useState(false);

  useEffect(() => {
    const savedMode = localStorage.getItem("darkMode") === "true";
    setIsDark(savedMode);
    if (savedMode) {
      document.documentElement.classList.add("dark");
    }
  }, []);

  const toggleDarkMode = () => {
    const newMode = !isDark;
    setIsDark(newMode);
    document.documentElement.classList.toggle("dark");
    localStorage.setItem("darkMode", String(newMode));
  };

  return (
    <div className="min-h-screen bg-secondary">
      <button onClick={toggleDarkMode} className="...">
        {isDark ? "☀️" : "🌙"}
      </button>
      {/* rest of login form */}
    </div>
  );
}
```

---

## 📚 Additional Resources

- **Router docs**: [React Router v6](https://reactrouter.com/en/main)
- **Theme usage**: See `THEME_QUICK_REFERENCE.md`
- **Examples**: See `THEME_USAGE_EXAMPLES.tsx`
- **Migration**: See `MIGRATION_EXAMPLE.md`

---

## ✅ Summary

Your setup is correct! Here's what's happening:

1. ✅ `main.tsx` renders `RouterProvider`
2. ✅ `router.tsx` defines all routes
3. ✅ `ProtectedLayout` provides navigation and dark mode
4. ✅ Individual page components render in `<Outlet />`
5. ✅ `App.css` provides the theme
6. ✅ No `App.tsx` needed - this is the modern way!

**You're following React Router v6 best practices perfectly!** 🎉
