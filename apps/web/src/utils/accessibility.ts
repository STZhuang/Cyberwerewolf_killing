/**
 * Accessibility utilities for better a11y support
 */

/**
 * Announce message to screen readers
 */
export function announceToScreenReader(message: string, priority: 'polite' | 'assertive' = 'polite'): void {
  const announcer = document.createElement('div')
  announcer.setAttribute('aria-live', priority)
  announcer.setAttribute('aria-atomic', 'true')
  announcer.setAttribute('class', 'sr-only')
  announcer.textContent = message

  document.body.appendChild(announcer)

  // Remove after announcement
  setTimeout(() => {
    document.body.removeChild(announcer)
  }, 1000)
}

/**
 * Focus management utility
 */
export class FocusManager {
  private focusHistory: HTMLElement[] = []

  /**
   * Save current focus and focus target element
   */
  focus(element: HTMLElement | null, savePrevious = true): void {
    if (savePrevious && document.activeElement instanceof HTMLElement) {
      this.focusHistory.push(document.activeElement)
    }

    if (element) {
      element.focus()
    }
  }

  /**
   * Restore previous focus
   */
  restoreFocus(): void {
    const previousElement = this.focusHistory.pop()
    if (previousElement) {
      previousElement.focus()
    }
  }

  /**
   * Focus first focusable element in container
   */
  focusFirstIn(container: HTMLElement): boolean {
    const focusable = this.getFocusableElements(container)
    if (focusable.length > 0) {
      focusable[0].focus()
      return true
    }
    return false
  }

  /**
   * Focus last focusable element in container
   */
  focusLastIn(container: HTMLElement): boolean {
    const focusable = this.getFocusableElements(container)
    if (focusable.length > 0) {
      focusable[focusable.length - 1].focus()
      return true
    }
    return false
  }

  /**
   * Get all focusable elements in container
   */
  getFocusableElements(container: HTMLElement): HTMLElement[] {
    const focusableSelectors = [
      'a[href]',
      'button:not([disabled])',
      'input:not([disabled])',
      'select:not([disabled])',
      'textarea:not([disabled])',
      '[tabindex]:not([tabindex="-1"])',
      '[contenteditable="true"]'
    ].join(', ')

    return Array.from(container.querySelectorAll(focusableSelectors))
      .filter(el => {
        return el instanceof HTMLElement && 
               !el.hasAttribute('aria-hidden') &&
               el.offsetWidth > 0 && 
               el.offsetHeight > 0
      }) as HTMLElement[]
  }

  /**
   * Trap focus within container
   */
  trapFocus(container: HTMLElement): () => void {
    const focusable = this.getFocusableElements(container)
    
    if (focusable.length === 0) {
      return () => {}
    }

    const firstFocusable = focusable[0]
    const lastFocusable = focusable[focusable.length - 1]

    const handleKeydown = (event: KeyboardEvent) => {
      if (event.key !== 'Tab') return

      if (event.shiftKey) {
        // Shift + Tab
        if (document.activeElement === firstFocusable) {
          event.preventDefault()
          lastFocusable.focus()
        }
      } else {
        // Tab
        if (document.activeElement === lastFocusable) {
          event.preventDefault()
          firstFocusable.focus()
        }
      }
    }

    container.addEventListener('keydown', handleKeydown)
    
    // Focus first element initially
    firstFocusable.focus()

    // Return cleanup function
    return () => {
      container.removeEventListener('keydown', handleKeydown)
    }
  }
}

/**
 * Keyboard navigation utilities
 */
export class KeyboardNavigation {
  /**
   * Handle arrow key navigation in a list
   */
  static handleArrowNavigation(
    event: KeyboardEvent,
    items: HTMLElement[],
    currentIndex: number,
    orientation: 'horizontal' | 'vertical' = 'vertical'
  ): number {
    let newIndex = currentIndex

    switch (event.key) {
      case 'ArrowUp':
        if (orientation === 'vertical') {
          event.preventDefault()
          newIndex = currentIndex > 0 ? currentIndex - 1 : items.length - 1
        }
        break
      case 'ArrowDown':
        if (orientation === 'vertical') {
          event.preventDefault()
          newIndex = currentIndex < items.length - 1 ? currentIndex + 1 : 0
        }
        break
      case 'ArrowLeft':
        if (orientation === 'horizontal') {
          event.preventDefault()
          newIndex = currentIndex > 0 ? currentIndex - 1 : items.length - 1
        }
        break
      case 'ArrowRight':
        if (orientation === 'horizontal') {
          event.preventDefault()
          newIndex = currentIndex < items.length - 1 ? currentIndex + 1 : 0
        }
        break
      case 'Home':
        event.preventDefault()
        newIndex = 0
        break
      case 'End':
        event.preventDefault()
        newIndex = items.length - 1
        break
    }

    if (newIndex !== currentIndex && items[newIndex]) {
      items[newIndex].focus()
    }

    return newIndex
  }
}

/**
 * ARIA utilities
 */
export class AriaUtils {
  /**
   * Set ARIA attributes for expandable content
   */
  static setExpandableAttributes(
    trigger: HTMLElement,
    content: HTMLElement,
    isExpanded: boolean
  ): void {
    const contentId = content.id || `expandable-content-${Math.random().toString(36).substr(2, 9)}`
    
    if (!content.id) {
      content.id = contentId
    }

    trigger.setAttribute('aria-expanded', isExpanded.toString())
    trigger.setAttribute('aria-controls', contentId)
    content.setAttribute('aria-hidden', (!isExpanded).toString())
  }

  /**
   * Set ARIA attributes for modal dialog
   */
  static setModalAttributes(
    modal: HTMLElement,
    labelledBy?: string,
    describedBy?: string
  ): void {
    modal.setAttribute('role', 'dialog')
    modal.setAttribute('aria-modal', 'true')
    
    if (labelledBy) {
      modal.setAttribute('aria-labelledby', labelledBy)
    }
    
    if (describedBy) {
      modal.setAttribute('aria-describedby', describedBy)
    }
  }

  /**
   * Create accessible description for game messages
   */
  static createMessageDescription(
    authorName: string,
    seat?: number,
    timestamp?: number,
    visibility?: string,
    content?: string
  ): string {
    const parts: string[] = []
    
    if (seat) {
      parts.push(`${seat}号玩家`)
    }
    
    parts.push(authorName)
    
    if (timestamp) {
      const timeStr = new Date(timestamp).toLocaleTimeString('zh-CN', {
        hour: '2-digit',
        minute: '2-digit'
      })
      parts.push(`在${timeStr}`)
    }
    
    if (visibility && visibility !== 'public') {
      const visibilityText = {
        'team': '向队伍',
        'private': '私密地',
        'system': '系统'
      }[visibility] || ''
      
      if (visibilityText) {
        parts.push(visibilityText)
      }
    }
    
    parts.push('说：')
    
    if (content) {
      parts.push(content.substring(0, 100))
      if (content.length > 100) {
        parts.push('...')
      }
    }
    
    return parts.join('')
  }
}

/**
 * Screen reader utilities
 */
export class ScreenReaderUtils {
  /**
   * Check if screen reader is likely being used
   */
  static isScreenReaderLikely(): boolean {
    return window.speechSynthesis !== undefined ||
           'speechSynthesis' in window ||
           navigator.userAgent.includes('NVDA') ||
           navigator.userAgent.includes('JAWS')
  }

  /**
   * Speak text using speech synthesis API
   */
  static speak(text: string, options: SpeechSynthesisUtteranceOptions = {}): void {
    if (!window.speechSynthesis) return

    const utterance = new SpeechSynthesisUtterance(text)
    
    Object.assign(utterance, {
      rate: 1,
      pitch: 1,
      volume: 1,
      ...options
    })

    window.speechSynthesis.speak(utterance)
  }

  /**
   * Stop all speech synthesis
   */
  static stopSpeaking(): void {
    if (window.speechSynthesis) {
      window.speechSynthesis.cancel()
    }
  }
}

/**
 * Color contrast utilities
 */
export class ContrastUtils {
  /**
   * Calculate relative luminance of RGB color
   */
  static getLuminance(r: number, g: number, b: number): number {
    const [rs, gs, bs] = [r, g, b].map(c => {
      c = c / 255
      return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4)
    })
    
    return 0.2126 * rs + 0.7152 * gs + 0.0722 * bs
  }

  /**
   * Calculate contrast ratio between two colors
   */
  static getContrastRatio(color1: [number, number, number], color2: [number, number, number]): number {
    const lum1 = this.getLuminance(...color1)
    const lum2 = this.getLuminance(...color2)
    
    const brightest = Math.max(lum1, lum2)
    const darkest = Math.min(lum1, lum2)
    
    return (brightest + 0.05) / (darkest + 0.05)
  }

  /**
   * Check if color combination meets WCAG AA standard
   */
  static meetsWCAGAA(foreground: [number, number, number], background: [number, number, number]): boolean {
    const ratio = this.getContrastRatio(foreground, background)
    return ratio >= 4.5
  }

  /**
   * Check if color combination meets WCAG AAA standard
   */
  static meetsWCAGAAA(foreground: [number, number, number], background: [number, number, number]): boolean {
    const ratio = this.getContrastRatio(foreground, background)
    return ratio >= 7
  }
}

// Create singleton instances
export const focusManager = new FocusManager()
export const ariaUtils = new AriaUtils()
export const screenReaderUtils = new ScreenReaderUtils()
export const contrastUtils = new ContrastUtils()

// Export default utilities object
export default {
  announceToScreenReader,
  FocusManager,
  KeyboardNavigation,
  AriaUtils,
  ScreenReaderUtils,
  ContrastUtils,
  focusManager,
  ariaUtils,
  screenReaderUtils,
  contrastUtils
}