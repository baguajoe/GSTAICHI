// // Video.js page to dynamically display embedded videos using a dedicated VideoComponent.
import React from 'react';
import VideoComponent from "../component/VideoComponent"
import Header from "../component/Header";


const videos = [
    { 
        src: 'https://player.vimeo.com/video/951751367?title=0&byline=0&portrait=0&badge=0&autopause=0&player_id=0&app_id=58479', 
        title: "Chen's 11 Tai Chi Chuan Techniques", 
        description: "The 11 techniques Tai Chi Chuan is not an abbreviated form, but a collection of 11 essential techniques practiced individually. Created by Chen Wei Ming (1881-1958), this method focuses on fundamental movements and mastery of individual techniques rather than teaching a choreographed sequence for beginners." 
    }
    ,
    { 
        src: 'https://player.vimeo.com/video/898123775?title=0&byline=0&portrait=0&badge=0&autopause=0&player_id=0&app_id=58479', 
        title: "Five Animals Frolics", 
        description: "Five Animal Frolics is a famous Daoyin exercise created by Hua Tuo during the Eastern Han Dynasty to promote qi and blood circulation, inspired by the principle of constant movement to prevent stagnation and illness." 
    }
    ,
    { 
        src: 'https://player.vimeo.com/video/568637507?title=0&byline=0&portrait=0&badge=0&autopause=0&player_id=0&app_id=58479', 
        title: "22 Technique Tai Chi Sword", 
        description: "For its gracefulness in motion, Tai Chi Sword is one of the most popular weapons in the Tai Chi Chuan System. The 22 Techniques Tai Chi Sword form, developed from traditional Yang Style Tai Chi Sword, emphasizes softness, elasticity, dynamic stepping, coordination, and the principle of body and mind unity through four structured sections tailored for various levels and ages." 
    }
    ,
    {
        src: 'https://player.vimeo.com/video/568640580?title=0&byline=0&portrait=0&badge=0&autopause=0&player_id=0&app_id=58479', 
        title: "Tai Chi Gong", 
        description: "Tai Chi Chuan has become a popular health-maintenance exercise, but its solo form can be difficult for new students to learn. To address this, Tai Chi Gong was created with exercises that are easy to learn, simple to practice, and designed to help students gradually build their Tai Chi foundation."
    },
    {
        src: 'https://player.vimeo.com/video/568661984?title=0&byline=0&portrait=0&badge=0&autopause=0&player_id=0&app_id=58479', 
        title: "Tai Chi Chuan Push Hands Exercises", 
        description: "Partner drill training in Chinese martial arts, including push hands exercises, is essential for understanding offensive and defensive techniques. Beginning with pre-programmed movements and progressing to randomized applications, push hands develop speed, power, and proper technique execution during combat simulations."
    }
    ,
    {
        src: 'https://player.vimeo.com/video/568640580?title=0&byline=0&portrait=0&badge=0&autopause=0&player_id=0&app_id=58479', 
        title: "Tai Chi Gong", 
        description: "Tai Chi Chuan has become a popular health-maintenance exercise, but its solo form can be difficult for new students to learn. To address this, Tai Chi Gong was created with exercises that are easy to learn, simple to practice, and designed to help students gradually build their Tai Chi foundation."
    }
    ,
    {
        src: 'https://player.vimeo.com/video/568657740?title=0&byline=0&portrait=0&badge=0&autopause=0&player_id=0&app_id=58479', 
        title: "Ba Duan Jin Qigong", 
        description: "In ancient China, many people pursued self-tempering exercises to enhance their well-being and extend longevity. Over time, these efforts led to the development of Ba Duan Jin Qigong, a traditional set of exercises focused on improving health and promoting vitality through disciplined practice."
    }
    ,
    {
        src: 'https://player.vimeo.com/video/569922509?title=0&byline=0&portrait=0&badge=0&autopause=0&player_id=0&app_id=58479', 
        title: "18 Techniques Medium Frame Solo Form", 
        description: "Due to physical limitations, Tai Chi Chuan movements are categorized into circular motions of different sizes—large, medium, and small. The 18 Techniques Medium Frame Tai Chi Chuan solo form is an abbreviated version of the traditional Yang Style, based on the teachings of Yeung Sau Chung, focusing on precision, balance, and martial applications."
    }
    ,
    {
        src: 'https://player.vimeo.com/video/569789187?title=0&byline=0&portrait=0&badge=0&autopause=0&player_id=0&app_id=58479', 
        title: "10 Techniques Large Circle Tai Chi Chuan Form", 
        description: "Due to physical limitations, Tai Chi Chuan movements use circular motions categorized as large, medium, or small. Large circles in Tai Chi Chuan emphasize expansive movement and flow, aiding in martial applications while supporting flexibility, strength, and broader body coordination."
    }
    ,
    {
        src: 'https://player.vimeo.com/video/568665316?title=0&byline=0&portrait=0&badge=0&autopause=0&player_id=0&app_id=58479', 
        title: "Tai Chi Chuan Fundamentals", 
        description: "Tai Chi Chuan is one of the treasures of China’s heritage, with a long history and valuable merits in self-defense, performance, health maintenance, and personal growth. Rooted in Tai Chi Yin-Yang philosophy, Lao Tzu's teachings, traditional Chinese medicine, martial arts principles, and life-nurturing arts, it offers a comprehensive approach to well-being."
    }
    ,
    {
        src: 'https://player.vimeo.com/video/715051860?title=0&byline=0&portrait=0&badge=0&autopause=0&player_id=0&app_id=58479', 
        title: "Internal Martial Art Eight Zhan Zhuang Techniques", 
        description: "The Internal Martial Art Eight Zhan Zhuang Techniques, also known as the universal stance, focus on both external support and internal qi circulation. Properly positioned stances enable the free flow of qi inside the body, promoting internal power accumulation through comfortable alignment and natural energy flow."
    },
    { src: 'https://player.vimeo.com/video/608292802?title=0&byline=0&portrait=0&badge=0&autopause=0&player_id=0&app_id=58479', title: "12 Techniques Returning Tai Chi Chuan Solo Form" },
    { src: 'https://player.vimeo.com/video/720756335?title=0&byline=0&portrait=0&badge=0&autopause=0&player_id=0&app_id=58479', title: "15 Techniques Small Solo Frame" },
    {
        src: 'https://player.vimeo.com/video/602311559?title=0&byline=0&portrait=0&badge=0&autopause=0&player_id=0&app_id=58479', 
        title: "Yang Style Tai Chi Chuan Medium Frame Solo Form Part 1", 
        description: "Tai Chi Chuan is one of the great treasures of Chinese culture, practiced globally for health, fitness, and meditation. As a gentle exercise, Tai Chi suits all physical conditions and ages, making it a lifelong practice for wellness."
    },
    
    {
        src: 'https://player.vimeo.com/video/803541958?title=0&byline=0&portrait=0&badge=0&autopause=0&player_id=0&app_id=58479', 
        title: "Yang Style Tai Chi Chuan Medium Frame Solo Form Part 2", 
        description: "Tai Chi Chuan, with its slow and relaxed movements, is ideal for fitness, meditation, and health maintenance. Practitioners can benefit from its gentle physical nature from youth through old age, maintaining vitality and balance."
    },
    {
        src: 'https://player.vimeo.com/video/638173692?title=0&byline=0&portrait=0&badge=0&autopause=0&player_id=0&app_id=58479', 
        title: "13 Animal Form: 13 Ways To Solidifying The Elixir Part 1", 
        description: "Among the Tai Chi Chuan forms, the Tai Chi 13 Dan Shi, or 13 Animals Form, is the oldest known form. Known as the 13 Ways of Solidifying the Elixir, it preserves ancient Tai Chi techniques that many contemporary practitioners rarely explore, making it a true cornerstone of the practice."
    },
    {
        src: 'https://player.vimeo.com/video/638185051?title=0&byline=0&portrait=0&badge=0&autopause=0&player_id=0&app_id=58479', 
        title: "13 Animal Form: 13 Ways To Solidifying The Elixir Part 2", 
        description: "The Tai Chi 13 Animals Form continues with its rich exploration of the oldest Tai Chi Chuan techniques. As a rare form practiced today, it emphasizes internal energy cultivation and mastery of traditional movements, preserving the foundation of Tai Chi for future generations."
    }
];

const Video = () => {
    return (
        <div>
            <Header />  {/* Add the header here */}
            <div className='d-flex flex-wrap'>
                {videos.map((video, index) => (
                    <VideoComponent key={index} src={video.src} description={video.description} title={video.title} />
                ))}
            </div>
        </div>
    );
};


export default Video;
