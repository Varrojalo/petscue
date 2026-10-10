import { Link } from "react-router";

import styles from "./Button.module.css";

/** Big, clear buttons. `to` makes it a link to another page; `href` a link to another site. */
export default function Button({ variant = "primary", size, block, to, href, className = "", children, ...rest }) {
  const classes = [styles.button, styles[variant], size === "small" && styles.small, block && styles.block, className]
    .filter(Boolean)
    .join(" ");
  if (to) return <Link to={to} className={classes} {...rest}>{children}</Link>;
  if (href) return <a href={href} className={classes} target="_blank" rel="noopener noreferrer" {...rest}>{children}</a>;
  return <button type="button" className={classes} {...rest}>{children}</button>;
}
