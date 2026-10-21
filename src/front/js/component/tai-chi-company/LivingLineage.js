import React from "react";
import { Link } from "react-router-dom";
import { vincentChu, teacherLine, school } from "../../utils/schoolInfo";

// The line of teachers from the founder of the Yang style to Vincent Chu, oldest first
export const TeacherLineStrip = () => (
    <ol className="tcc-lineage-strip" aria-label="Lineage, from the founder of the Yang style to Vincent Chu">
        {teacherLine.map(person => (
            <li key={person.name} className="tcc-lineage-person">
                {person.image && <img src={person.image} alt="" className="tcc-lineage-photo" />}
                <span className="tcc-lineage-name">{person.name}</span>
                {person.lifespan && <span className="tcc-lineage-years">{person.lifespan}</span>}
            </li>
        ))}
    </ol>
);

// Landing page section: the teacher, the lineage and the school in one short block
const LivingLineage = () => (
    <section className="tcc-section tcc-living-lineage">
        <h2>Learn from a living lineage</h2>
        <div className="tcc-teacher-intro">
            <img src={vincentChu.image} alt={vincentChu.name} className="tcc-teacher-photo" />
            <div>
                <h3>{vincentChu.name}</h3>
                <p>{vincentChu.shortBio}</p>
                <Link to="/tai-chi-company/about" className="tcc-text-link">Read more about your teacher</Link>
            </div>
        </div>
        <TeacherLineStrip />
        <p className="tcc-school-line">{school.summary}</p>
    </section>
);

export default LivingLineage;
