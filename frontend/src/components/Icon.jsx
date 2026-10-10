const PATHS = {
  home: <><path d="M3 11l9-7 9 7" /><path d="M5 10v10h14V10" /><path d="M10 20v-5h4v5" /></>,
  paw: <><circle cx="6.5" cy="10" r="2" /><circle cx="10" cy="5.5" r="2" /><circle cx="14" cy="5.5" r="2" /><circle cx="17.5" cy="10" r="2" /><path d="M8 17.5c0-3 2-5.5 4-5.5s4 2.5 4 5.5c0 2-1.8 2.5-4 2.5s-4-.5-4-2.5z" /></>,
  heart: <path d="M12 20s-7.5-4.6-7.5-10.2A4.3 4.3 0 0 1 12 7a4.3 4.3 0 0 1 7.5 2.8C19.5 15.4 12 20 12 20z" />,
  hand: <><path d="M7 11V6.5a1.5 1.5 0 0 1 3 0V11" /><path d="M10 10V5a1.5 1.5 0 0 1 3 0v5" /><path d="M13 10V6a1.5 1.5 0 0 1 3 0v6" /><path d="M16 11.5a1.5 1.5 0 0 1 3 0V15a6 6 0 0 1-6 6h-1a6 6 0 0 1-5-2.7L4.5 14.6a1.5 1.5 0 0 1 2.4-1.8L7 13" /></>,
  pin: <><path d="M12 21s-7-6.2-7-11.5a7 7 0 0 1 14 0C19 14.8 12 21 12 21z" /><circle cx="12" cy="9.5" r="2.5" /></>,
  arrow: <path d="M5 12h14M13 6l6 6-6 6" />,
  back: <path d="M19 12H5M11 6l-6 6 6 6" />,
  camera: <><path d="M4 8h3.2l1.8-3h6l1.8 3H20v11H4z" /><circle cx="12" cy="13" r="3.5" /></>,
  share: <><circle cx="6" cy="12" r="2.5" /><circle cx="18" cy="6" r="2.5" /><circle cx="18" cy="18" r="2.5" /><path d="M8.2 10.8l7.6-3.6M8.2 13.2l7.6 3.6" /></>,
  house: <><path d="M3 11l9-7 9 7" /><path d="M5 10v10h14V10" /><path d="M9.5 15.5c0-1.4 1.1-2.5 2.5-2.5s2.5 1.1 2.5 2.5" /></>,
  info: <><circle cx="12" cy="12" r="9" /><path d="M12 11v5.5M12 7.5v.01" /></>,
  check: <path d="M5 12.5l4.5 4.5L19 7.5" />,
  chart: <><path d="M4 20V11" /><path d="M10 20V5" /><path d="M16 20v-7" /><path d="M21 20H3" /></>,
  eye: <><path d="M2 12s3.6-7 10-7 10 7 10 7-3.6 7-10 7S2 12 2 12z" /><circle cx="12" cy="12" r="3" /></>,
  logout: <><path d="M15 4h4v16h-4" /><path d="M10 8l-4 4 4 4" /><path d="M6 12h10" /></>,
  more: <><circle cx="5" cy="12" r="1.5" /><circle cx="12" cy="12" r="1.5" /><circle cx="19" cy="12" r="1.5" /></>,
  plus: <path d="M12 5v14M5 12h14" />,
  edit: <><path d="M4 20h4L19 9l-4-4L4 16z" /><path d="M13.5 6.5l4 4" /></>,
  star: <path d="M12 3.5l2.6 5.4 5.9.8-4.3 4.1 1 5.8L12 16.8l-5.2 2.8 1-5.8-4.3-4.1 5.9-.8z" />,
  undo: <><path d="M9 14L4 9l5-5" /><path d="M4 9h10a6 6 0 0 1 0 12h-2" /></>,
  clock: <><circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 2" /></>,
  trash: <><path d="M4 7h16" /><path d="M9 7V4h6v3" /><path d="M6 7l1 13h10l1-13" /></>,
  up: <path d="M12 19V5M6 11l6-6 6 6" />,
  down: <path d="M12 5v14M6 13l6 6 6-6" />,
  search: <><circle cx="11" cy="11" r="7" /><path d="M20 20l-4-4" /></>,
};

export default function Icon({ name, size = "1.2em" }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ flex: "none" }}>
      {PATHS[name]}
    </svg>
  );
}
