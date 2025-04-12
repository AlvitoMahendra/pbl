-- phpMyAdmin SQL Dump
-- version 5.2.0
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Waktu pembuatan: 12 Apr 2025 pada 04.58
-- Versi server: 10.4.27-MariaDB
-- Versi PHP: 8.2.0

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `pblrks2`
--

-- --------------------------------------------------------

--
-- Struktur dari tabel `tb_contacts`
--

CREATE TABLE `tb_contacts` (
  `id` int(11) NOT NULL,
  `user_id` int(11) DEFAULT NULL,
  `contact_id` int(11) DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;

--
-- Dumping data untuk tabel `tb_contacts`
--

INSERT INTO `tb_contacts` (`id`, `user_id`, `contact_id`, `created_at`) VALUES
(3, 45, 47, '2025-04-11 06:01:00'),
(7, 46, 45, '2025-03-22 07:10:02'),
(11, 45, 46, '2025-03-22 08:18:26'),
(12, 47, 45, '2025-04-11 06:01:35'),
(14, 47, 46, '2025-04-11 10:42:49'),
(15, 47, 48, '2025-04-11 11:46:16'),
(16, 48, 47, '2025-04-11 11:47:54'),
(17, 49, 47, '2025-04-11 17:06:42'),
(18, 47, 49, '2025-04-11 17:07:39');

-- --------------------------------------------------------

--
-- Struktur dari tabel `tb_info_user`
--

CREATE TABLE `tb_info_user` (
  `id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `fullname` varchar(255) NOT NULL,
  `username` varchar(255) DEFAULT NULL,
  `email` varchar(255) NOT NULL,
  `level` varchar(255) DEFAULT NULL,
  `birthday` date DEFAULT NULL,
  `address` text DEFAULT NULL,
  `nohp` varchar(15) DEFAULT NULL,
  `city` varchar(255) DEFAULT NULL,
  `state` varchar(255) DEFAULT NULL,
  `country` varchar(255) DEFAULT NULL,
  `linked` varchar(255) DEFAULT NULL,
  `created` date NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;

--
-- Dumping data untuk tabel `tb_info_user`
--

INSERT INTO `tb_info_user` (`id`, `user_id`, `fullname`, `username`, `email`, `level`, `birthday`, `address`, `nohp`, `city`, `state`, `country`, `linked`, `created`) VALUES
(29, 45, 'Client 1 PBL 2', 'client1', 'client1@gmail.com', 'USER', NULL, NULL, NULL, NULL, NULL, NULL, NULL, '2025-03-22'),
(30, 46, 'Client2PBL', 'client2', 'client2@gmail.com', 'USER', NULL, NULL, NULL, NULL, NULL, NULL, NULL, '2025-03-22'),
(31, 47, 'ROOT', 'ROOT', 'root@gmail.com', 'USER', NULL, NULL, NULL, NULL, NULL, NULL, NULL, '2025-04-11'),
(32, 48, 'admin', 'admin', 'admin@gmail.com', 'USER', NULL, NULL, NULL, NULL, NULL, NULL, NULL, '2025-04-11'),
(33, 49, 'Rist', 'Ris', 'qweqweq@gmail.com', 'USER', '2222-02-22', 'ohioski', '22222222', 'ohio', 'asia', 'ohio', NULL, '2025-04-12');

-- --------------------------------------------------------

--
-- Struktur dari tabel `tb_messages`
--

CREATE TABLE `tb_messages` (
  `id` int(11) NOT NULL,
  `sender` varchar(255) DEFAULT NULL,
  `receiver` varchar(255) DEFAULT NULL,
  `message` text DEFAULT NULL,
  `timestamp` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;

--
-- Dumping data untuk tabel `tb_messages`
--

INSERT INTO `tb_messages` (`id`, `sender`, `receiver`, `message`, `timestamp`) VALUES
(70, 'client2', 'client1', 'test', '2025-03-22 08:18:26'),
(71, 'client1', 'client2', 'masuk client 2', '2025-03-22 08:19:02'),
(72, 'client1', 'client2', 'test', '2025-04-11 05:58:20'),
(73, 'client1', 'ROOT', 'HAHA AKU', '2025-04-11 06:01:35'),
(74, 'ROOT', 'client1', 'IYA KAMU SIAPA', '2025-04-11 06:01:54'),
(75, 'client1', 'ROOT', 'AKU GATAU AKU SIAPA', '2025-04-11 06:02:27'),
(76, 'ROOT', 'admin', 'haiii', '2025-04-11 11:47:54'),
(77, 'Ris', 'ROOT', '????', '2025-04-11 17:07:39'),
(78, 'Ris', 'ROOT', 'p', '2025-04-11 17:07:49'),
(79, 'ROOT', 'Ris', 'awuebfwa;', '2025-04-11 17:07:54'),
(80, 'Ris', 'ROOT', 'nampak', '2025-04-11 17:08:01');

-- --------------------------------------------------------

--
-- Struktur dari tabel `tb_user`
--

CREATE TABLE `tb_user` (
  `id` int(99) NOT NULL,
  `username` varchar(255) NOT NULL,
  `email` varchar(255) NOT NULL,
  `level` enum('USER','ADMIN') NOT NULL,
  `password` varchar(255) NOT NULL,
  `socket_id` varchar(255) DEFAULT NULL,
  `fullname` varchar(255) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;

--
-- Dumping data untuk tabel `tb_user`
--

INSERT INTO `tb_user` (`id`, `username`, `email`, `level`, `password`, `socket_id`, `fullname`) VALUES
(45, 'client1', 'client1@gmail.com', 'USER', 'scrypt:32768:8:1$LDvjrUJDtouQVhM3$38f350284591bb0472dba2a74f164aa8c963f9008eb871986e25f5fb6f0e802bb64d6d4f8e9878602fb72ded3b48aaed808d26051fad036e6da18f2a9bb15342', '2ljR43Ww4wvR8mxmAAA_', 'Client 1 PBL 2'),
(46, 'client2', 'client2@gmail.com', 'USER', 'scrypt:32768:8:1$2Pg8XYu9OY74lx2k$afc754cf56de4834594b94879d7e9ab7275a2e2be89141a7ddfe1309c378c5ca838143b6a52cb8b5d9e37ae31047f62d866ea312dda4eb16fccd1073f3e04229', NULL, 'Client2PBL'),
(47, 'ROOT', 'root@gmail.com', 'USER', 'scrypt:32768:8:1$evmCZOxIytuneGCZ$f7eea422d87a673347fbcb8937b196291774de54d726ee4188f1565df66bdc168d507b613cadb22af20c16cfab8658ea1c6ca919c141eb9ef8d3ac13dd714feb', NULL, 'ROOT'),
(48, 'admin', 'admin@gmail.com', 'USER', 'scrypt:32768:8:1$M3PvM7KByCx9Hhqg$18078a5a34f4843f5728291347e0080649a2b7cd8301663f1e61dd0f1ec4b8f94a41bccd9c083984ede717133c6dd54166ed66b4c5b2bcbf9854cff780b8ed87', NULL, 'admin'),
(49, 'Ris', 'qweqweq@gmail.com', 'USER', 'scrypt:32768:8:1$SIjuQRpxAQk1WMrX$81fafa0e9c310256724c3d75b2955bdc4b3f160692f1dfd46275a95c13766967a7f27aa6de206f009b90cb155b5a3e1cd5511f798cfcf213284dbac6f2870370', NULL, 'Rist');

--
-- Indexes for dumped tables
--

--
-- Indeks untuk tabel `tb_contacts`
--
ALTER TABLE `tb_contacts`
  ADD PRIMARY KEY (`id`),
  ADD KEY `user_id` (`user_id`),
  ADD KEY `contact_id` (`contact_id`);

--
-- Indeks untuk tabel `tb_info_user`
--
ALTER TABLE `tb_info_user`
  ADD PRIMARY KEY (`id`),
  ADD KEY `user_id` (`user_id`),
  ADD KEY `fk_info_user_fullname` (`fullname`),
  ADD KEY `idx_email` (`email`);

--
-- Indeks untuk tabel `tb_messages`
--
ALTER TABLE `tb_messages`
  ADD PRIMARY KEY (`id`);

--
-- Indeks untuk tabel `tb_user`
--
ALTER TABLE `tb_user`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `fullname` (`fullname`),
  ADD UNIQUE KEY `unique_email` (`email`);

--
-- AUTO_INCREMENT untuk tabel yang dibuang
--

--
-- AUTO_INCREMENT untuk tabel `tb_contacts`
--
ALTER TABLE `tb_contacts`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=19;

--
-- AUTO_INCREMENT untuk tabel `tb_info_user`
--
ALTER TABLE `tb_info_user`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=34;

--
-- AUTO_INCREMENT untuk tabel `tb_messages`
--
ALTER TABLE `tb_messages`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=81;

--
-- AUTO_INCREMENT untuk tabel `tb_user`
--
ALTER TABLE `tb_user`
  MODIFY `id` int(99) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=50;

--
-- Ketidakleluasaan untuk tabel pelimpahan (Dumped Tables)
--

--
-- Ketidakleluasaan untuk tabel `tb_contacts`
--
ALTER TABLE `tb_contacts`
  ADD CONSTRAINT `tb_contacts_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `tb_user` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `tb_contacts_ibfk_2` FOREIGN KEY (`contact_id`) REFERENCES `tb_user` (`id`) ON DELETE CASCADE;

--
-- Ketidakleluasaan untuk tabel `tb_info_user`
--
ALTER TABLE `tb_info_user`
  ADD CONSTRAINT `fk_info_user_email` FOREIGN KEY (`email`) REFERENCES `tb_user` (`email`) ON DELETE CASCADE ON UPDATE CASCADE,
  ADD CONSTRAINT `fk_info_user_fullname` FOREIGN KEY (`fullname`) REFERENCES `tb_user` (`fullname`) ON DELETE CASCADE ON UPDATE CASCADE,
  ADD CONSTRAINT `tb_info_user_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `tb_user` (`id`) ON DELETE CASCADE;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
