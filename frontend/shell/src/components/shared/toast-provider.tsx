import { Toaster } from '@/components/ui/sonner'

export function ToastProvider() {
  return (
    <Toaster
      position='bottom-right'
      toastOptions={{
        classNames: {
          toast: 'bg-card border-border text-foreground',
          description: 'text-muted-foreground',
        },
      }}
    />
  )
}
