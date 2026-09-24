import "./globals.css";

export const metadata = {
  title: "Instant Mechanic — AI Car Diagnosis",
  description: "Chat with a virtual senior automobile technician for car troubleshooting and diagnosis.",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
