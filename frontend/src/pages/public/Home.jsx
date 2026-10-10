import { Link } from "react-router";

import { getAnimals, getStats } from "../../api/public";
import Button from "../../components/Button";
import Icon from "../../components/Icon";
import { ErrorMessage, Loading } from "../../components/PageState";
import Photo from "../../components/Photo";
import Underline from "../../components/Underline";
import { age, money } from "../../lib/format";
import { useApi } from "../../lib/useApi";
import { useOrganization } from "../../organization/OrganizationProvider";
import styles from "./Home.module.css";

function FeeBox({ fee }) {
  return (
    <div className={styles.fee}>
      {fee > 0 ? (
        <>
          <p>La adopción tiene un aporte de <b>{money(fee)}</b>. Se paga a la fundación al firmar el contrato y ayuda a cuidar al resto de los animales.</p>
          <b className={styles.feeAmount}>{money(fee)}</b>
        </>
      ) : (
        <p>Adoptar no tiene costo. El trabajo de la fundación se financia con el aporte de sus socios.</p>
      )}
    </div>
  );
}

export default function Home() {
  const { organization } = useOrganization();
  const animals = useApi(() => getAnimals());
  const stats = useApi(getStats);

  if (animals.loading || !organization) return <Loading />;
  if (animals.error) return <ErrorMessage error={animals.error} />;

  const list = animals.data.items;
  const featured = list.find((a) => a.slug === organization.featured_animal?.slug) || list[0];
  const others = list.filter((a) => a !== featured).slice(0, 3);
  const minSponsorship = organization.membership_tiers[0]?.monthly_amount;

  return (
    <>
      <section className={styles.hero}>
        {featured && (
          <Link to={`/animales/${featured.slug}`} className={styles.feature}>
            <Photo photo={featured.cover} seed={featured.id} alt={`Foto de ${featured.name}`} large className={styles.featurePhoto} />
            <span className={styles.shade} />
            <span className={styles.featureCopy}>
              <small>Busca familia · {age(featured.age_months)}</small>
              <span className={styles.featureName}><Underline>{featured.name}</Underline></span>
              <span className={styles.go}>Conocer a {featured.name} <Icon name="arrow" /></span>
            </span>
          </Link>
        )}
        <div className={styles.heroSide}>
          <p className={styles.eyebrow}>{organization.name}{organization.locality ? ` · ${organization.locality}` : ""}</p>
          <h1>Tu próximo compañero ya te está esperando</h1>
          <p className={styles.lede}>
            {list.length > 0
              ? `Tenemos ${animals.data.count} ${animals.data.count === 1 ? "animal listo" : "animales listos"} para ir a casa. Conócelos, súmate como socio o como voluntario.`
              : "Pronto publicaremos a los animales que buscan familia. Mientras tanto, puedes sumarte como socio o voluntario."}
          </p>
          {list.length > 0 && <Button to="/animales">Ver a todos <Icon name="arrow" /></Button>}
          {stats.data && (
            <div className={styles.stats}>
              <div><b>{stats.data.adoptions_this_year}</b><span>adopciones este año</span></div>
              <div><b>{stats.data.active_members}</b><span>socios nos apoyan</span></div>
            </div>
          )}
        </div>
      </section>

      {others.length > 0 && (
        <section className={styles.fanWrap}>
          <div className={styles.stack}>
            <h2 className={styles.sectionTitle}>También buscan casa</h2>
            <p className={styles.muted}>Toca a cualquiera para conocer su historia.</p>
            <Link to="/animales" className={styles.link}>Ver todos <Icon name="arrow" /></Link>
          </div>
          <div className={styles.fan}>
            {others.map((animal, i) => (
              <Link key={animal.id} to={`/animales/${animal.slug}`} className={`${styles.fanCard} ${styles[`c${i}`]}`}>
                <span className={styles.fanPhoto}><Photo photo={animal.cover} seed={animal.id} alt={`Foto de ${animal.name}`} /></span>
                <b>{animal.name}</b>
                <small>{age(animal.age_months)}</small>
              </Link>
            ))}
          </div>
        </section>
      )}

      <section className={styles.stack}>
        <h2 className={styles.sectionTitle}>Otras formas de ayudar</h2>
        <div className={styles.ways}>
          <Link to="/ayudar?como=socio" className={`${styles.way} ${styles.wayAccent}`}>
            <span className={styles.bubble}><Icon name="heart" size="26" /></span>
            <span>
              <b>Hazte socio</b>
              <small>{minSponsorship ? `Aporta a la fundación desde ${money(minSponsorship)} al mes` : "Aporta a la fundación"} o apadrina a un animal</small>
            </span>
            <span className={styles.arrow}><Icon name="arrow" /></span>
          </Link>
          <Link to="/ayudar?como=voluntario" className={styles.way}>
            <span className={styles.bubble}><Icon name="hand" size="26" /></span>
            <span>
              <b>Hazte voluntario</b>
              <small>Aporta tu tiempo en el refugio y las ferias. Las casas de acogida salen del equipo</small>
            </span>
            <span className={styles.arrow}><Icon name="arrow" /></span>
          </Link>
        </div>
      </section>

      <section className={styles.stack}>
        <h2 className={styles.sectionTitle}>Cómo es adoptar</h2>
        <ol className={styles.steps}>
          <li><b>Elige</b><p>Mira las fichas y encuentra a tu compañero.</p></li>
          <li><b>Envía tu solicitud</b><p>Solo tus datos básicos. Tardas dos minutos.</p></li>
          <li><b>Conversemos</b><p>Te llamamos y coordinamos una visita para que se conozcan.</p></li>
          <li><b>Firma y a casa</b><p>Se va con chip, vacunas y esterilización al día.</p></li>
        </ol>
        <FeeBox fee={organization.adoption_fee} />
      </section>
    </>
  );
}
