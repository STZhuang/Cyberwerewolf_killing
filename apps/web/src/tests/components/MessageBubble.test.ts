import { describe, it, expect, beforeEach } from 'vitest'
import { mount } from '@vue/test-library'
import MessageBubble from '@/components/Timeline/MessageBubble.vue'
import type { MessageBubbleProps } from '@/types/game'

describe('MessageBubble', () => {
  let defaultProps: MessageBubbleProps

  beforeEach(() => {
    defaultProps = {
      id: 'msg-1',
      seat: 1,
      authorName: 'TestUser',
      visibility: 'public',
      phase: 'DayTalk',
      timestamp: Date.now(),
      status: 'final',
      content: {
        text: 'Hello, this is a test message'
      }
    }
  })

  it('renders basic message correctly', () => {
    const wrapper = mount(MessageBubble, {
      props: defaultProps
    })

    expect(wrapper.text()).toContain('TestUser')
    expect(wrapper.text()).toContain('Hello, this is a test message')
    expect(wrapper.find('[data-testid="message-bubble"]')).toBeTruthy()
  })

  it('shows correct visibility indicator', () => {
    const wrapper = mount(MessageBubble, {
      props: {
        ...defaultProps,
        visibility: 'team'
      }
    })

    expect(wrapper.find('[data-testid="visibility-indicator"]')).toBeTruthy()
    expect(wrapper.text()).toContain('队内')
  })

  it('renders streaming status correctly', () => {
    const wrapper = mount(MessageBubble, {
      props: {
        ...defaultProps,
        status: 'streaming',
        content: {
          text: { chunks: ['Hello', ' world', '...'] }
        }
      }
    })

    expect(wrapper.find('[data-testid="streaming-indicator"]')).toBeTruthy()
    expect(wrapper.text()).toContain('Hello world...')
  })

  it('shows error state', () => {
    const wrapper = mount(MessageBubble, {
      props: {
        ...defaultProps,
        status: 'error'
      }
    })

    expect(wrapper.find('[data-testid="error-indicator"]')).toBeTruthy()
    expect(wrapper.classes()).toContain('message-error')
  })

  it('renders vote summary block', () => {
    const wrapper = mount(MessageBubble, {
      props: {
        ...defaultProps,
        content: {
          blocks: [{
            type: 'vote_summary',
            votes: [
              { from: 1, to: 2 },
              { from: 2, to: 3 },
              { from: 3, to: null }
            ]
          }]
        }
      }
    })

    expect(wrapper.find('[data-testid="vote-summary"]')).toBeTruthy()
  })

  it('handles system messages differently', () => {
    const wrapper = mount(MessageBubble, {
      props: {
        ...defaultProps,
        visibility: 'system',
        authorName: 'System',
        seat: undefined
      }
    })

    expect(wrapper.classes()).toContain('message-system')
  })

  it('has proper accessibility attributes', () => {
    const wrapper = mount(MessageBubble, {
      props: defaultProps
    })

    const messageElement = wrapper.find('[data-testid="message-bubble"]')
    expect(messageElement.attributes('role')).toBe('article')
    expect(messageElement.attributes('aria-label')).toContain('TestUser')
  })

  it('renders markdown content', () => {
    const wrapper = mount(MessageBubble, {
      props: {
        ...defaultProps,
        content: {
          blocks: [{
            type: 'markdown',
            content: '**Bold text** and *italic text*'
          }]
        }
      }
    })

    expect(wrapper.find('[data-testid="markdown-content"]')).toBeTruthy()
  })

  it('shows action buttons when provided', () => {
    const mockAction = vi.fn()
    const wrapper = mount(MessageBubble, {
      props: {
        ...defaultProps,
        actions: [{
          label: 'Reply',
          onClick: mockAction
        }]
      }
    })

    const actionButton = wrapper.find('[data-testid="message-action"]')
    expect(actionButton).toBeTruthy()
    expect(actionButton.text()).toContain('Reply')
  })
})