import { ButtonHTMLAttributes, ReactNode } from 'react';
import { cx } from './ui';

type Variant = 'primary' | 'quiet' | 'allow' | 'block';

/**
 * Pushable "plate" button: a chamfered face over a darker edge that drops on press
 * (pattern after Josh Comeau's 3D button write-up). Used for actions that change state;
 * plain text buttons are used for navigation and filters.
 */
export default function PlateButton({
  variant = 'primary',
  size = 'md',
  children,
  className,
  type = 'button',
  ...rest
}: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: Variant; size?: 'sm' | 'md'; children: ReactNode }) {
  return (
    <button
      type={type}
      className={cx('plate', variant !== 'primary' && `plate--${variant}`, size === 'sm' && 'plate--sm', className)}
      {...rest}
    >
      <span className="plate-edge" aria-hidden />
      <span className="plate-face">{children}</span>
    </button>
  );
}
