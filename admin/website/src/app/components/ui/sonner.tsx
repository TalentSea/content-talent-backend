import { Toaster as Sonner, ToasterProps } from "sonner";

const Toaster = ({ ...props }: ToasterProps) => {
  return (
    <Sonner
      className="toaster group"
      position="top-right"
      richColors
      closeButton
      duration={3000}
      toastOptions={{
        duration: 3000,
        className: "font-sans text-xs font-medium shadow-xl rounded-xl",
      }}
      {...props}
    />
  );
};

export { Toaster };

