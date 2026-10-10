import { useState } from "react";
import { useLocation, useNavigate, useParams } from "react-router";

import { getAnimal } from "../../api/public";
import Button from "../../components/Button";
import Icon from "../../components/Icon";
import { Empty, ErrorMessage, Loading } from "../../components/PageState";
import Photo from "../../components/Photo";
import { age, money } from "../../lib/format";
import { useApi } from "../../lib/useApi";
import { useOrganization } from "../../organization/OrganizationProvider";
import styles from "./AnimalDetail.module.css";

function ShareButton({ name }) {
  const [copied, setCopied] = useState(false);
  const share = async () => {
    const url = window.location.href;
    if (navigator.share) {
      try {
        await navigator.share({ title: name, url });
        return;
      } catch {
        /* closed by the person, or not available: fall back to copying */
      }
    }
    try {
      await navigator.clipboard.writeText(url);
      setCopied(true);
      setTimeout(() => setCopied(false), 3000);
    } catch {
      window.prompt("Copia este enlace:", url);
    }
  };
  return (
    <Button variant="ghost" block onClick={share}>
      <Icon name="share" /> {copied ? "Enlace copiado" : `Compartir la ficha de ${name}`}
    </Button>
  );
}

export default function AnimalDetail() {
  const { slug } = useParams();
  const navigate = useNavigate();
  const location = useLocation();
  // Coming from another page of the site: go back to it. Opened from a shared link: go to the list.
  const goBack = () => (location.key !== "default" ? navigate(-1) : navigate("/animales"));
  const { organization } = useOrganization();
  const { data: animal, error, loading } = useApi(() => getAnimal(slug), [slug]);
  const [current, setCurrent] = useState(0);

  if (loading) return <Loading />;
  if (error?.status === 410 || error?.status === 404) {
    return (
      <Empty title={error.status === 410 ? "Esta ficha ya no está disponible" : "No encontramos este animal"}>
        <p>Puedes conocer a los demás animales que buscan familia.</p>
        <Button to="/animales">Ver animales</Button>
      </Empty>
    );
  }
  if (error) return <ErrorMessage error={error} />;

  const female = animal.sex === "Hembra";
  const photo = animal.photos[current];
  const fee = organization?.adoption_fee || 0;

  return (
    <article className={styles.page}>
      <div className={styles.gallery}>
        <div className={styles.mainPhoto}>
          <Photo photo={photo} seed={animal.id} alt={`Foto de ${animal.name}`} large />
          <button type="button" className={styles.back} onClick={goBack}>
            <Icon name="back" /> Volver
          </button>
        </div>
        {animal.photos.length > 1 && (
          <div className={styles.thumbs}>
            {animal.photos.map((p, i) => (
              <button key={p.id} type="button" aria-pressed={i === current} onClick={() => setCurrent(i)} aria-label={`Ver foto ${i + 1}`}>
                <Photo photo={p} seed={animal.id} alt="" />
              </button>
            ))}
          </div>
        )}
      </div>

      <div className={styles.body}>
        {animal.in_foster_home ? (
          <span className={`${styles.pill} ${styles.foster}`}>En casa de acogida · disponible</span>
        ) : animal.in_treatment ? (
          <span className={`${styles.pill} ${styles.treatment}`}>En tratamiento</span>
        ) : (
          <span className={`${styles.pill} ${styles.available}`}>Disponible</span>
        )}
        <h1>{animal.name}</h1>
        {animal.quote && <p className={styles.quote}>“{animal.quote}”</p>}
        {animal.story && <p className={styles.story}>{animal.story}</p>}
        {animal.traits.length > 0 && (
          <div className={styles.traits}>
            {animal.traits.map((t) => <span key={t}>{t}</span>)}
          </div>
        )}
        <dl className={styles.facts}>
          <div><dt>Edad</dt><dd>{age(animal.age_months)}{animal.life_stage ? ` · ${animal.life_stage}` : ""}</dd></div>
          <div><dt>Tamaño</dt><dd>{animal.size}</dd></div>
          <div><dt>Sexo</dt><dd>{animal.sex}</dd></div>
          <div><dt>Vacunas</dt><dd>{animal.vaccinated ? "Al día" : "Pendientes"}</dd></div>
          <div><dt>Esterilización</dt><dd>{animal.sterilized ? "Sí" : "Pendiente"}</dd></div>
          <div><dt>Microchip</dt><dd>{animal.has_microchip ? "Sí" : "Pendiente"}</dd></div>
        </dl>
        {animal.in_foster_home && (
          <p className={styles.callout}>
            <Icon name="house" /> {animal.name} vive temporalmente con una familia de acogida. Si quieres {female ? "adoptarla" : "adoptarlo"}, la fundación coordina para que se conozcan.
          </p>
        )}
        <div className={styles.money}>
          <span>Aporte de adopción</span>
          <b>{fee > 0 ? money(fee) : "Sin costo"}</b>
        </div>
        <div className={styles.actions}>
          <Button block to={`/animales/${animal.slug}/adoptar`}>
            Quiero {female ? "adoptarla" : "adoptarlo"} <Icon name="arrow" />
          </Button>
          {animal.sponsorship_amount > 0 && (
            <Button block variant="accent" to={`/ayudar?como=padrino&animal=${animal.id}`}>
              Apadrinar · {money(animal.sponsorship_amount)} al mes
            </Button>
          )}
          <ShareButton name={animal.name} />
        </div>
      </div>
    </article>
  );
}
