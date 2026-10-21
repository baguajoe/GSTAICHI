import React from "react";
import { Link } from "react-router-dom";
import { ginSoonChu, vincentChu, teacherLineAncestors, school } from "../../utils/schoolInfo";
import { TeacherLineStrip } from "../../component/tai-chi-company/LivingLineage";

const Person = ({ person }) => (
    <article className="tcc-about-person">
        <img src={person.image} alt={person.name} className="tcc-about-photo" />
        <div>
            <h3>{person.name}</h3>
            {person.lifespan && <p className="tcc-about-years">{person.lifespan}</p>}
            <p>{person.bio || person.description}</p>
        </div>
    </article>
);

const About = () => (
    <div className="tcc-page tcc-about">
        <h1>About</h1>

        <section className="tcc-section">
            <h2>Your teacher</h2>
            <Person person={vincentChu} />
            <Person person={ginSoonChu} />
        </section>

        <section className="tcc-section">
            <h2>A living lineage</h2>
            <p>The Yang style of Tai Chi Chuan has been passed from teacher to student since its founder, Yang Lu Chan:</p>
            <TeacherLineStrip />
            {teacherLineAncestors.map(person => <Person key={person.key} person={person} />)}
            <p><a href="/lineage" className="tcc-text-link">See the full Yang family lineage</a></p>
        </section>

        <section className="tcc-section">
            <h2>The school</h2>
            <p>{school.founded}</p>
            <p>{school.difference}</p>
            <p>{school.federation}</p>
            <div className="tcc-notice">
                <h3>Visit the school</h3>
                <p>
                    {school.address.map(line => <React.Fragment key={line}>{line}<br /></React.Fragment>)}
                    Phone: <a href={`tel:${school.phone.replace(/[^\d+]/g, "")}`}>{school.phone}</a><br />
                    Email: <a href={`mailto:${school.email}`}>{school.email}</a>
                </p>
            </div>
        </section>

        <section className="tcc-section tcc-center">
            <Link to="/tai-chi-company/library" className="custom-btn1 tcc-btn tcc-btn-big">Go to the Library</Link>
        </section>
    </div>
);

export default About;
